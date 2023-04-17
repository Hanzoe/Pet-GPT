from .crazy_utils import read_and_clean_pdf_text
import time
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import QThread
from ..openai_request import OpenAI_request

class PDFAnalyzer:
    def __init__(self, chat_dialog_body,config):
        self.chat_dialog_body = chat_dialog_body
        #使用一个信号量来控制分段发送的信息，只有上一个请求释放了钥匙，才能进行下一个
        self.key = 1
        self.open_ai = OpenAI_request(config)
         # 将 tools_handle_response 函数连接到 chat_dialog_body.open_ai.tools_received 信号
        self.open_ai.tools_received.connect(self.tools_handle_response)
        # 创建新线程发出http请求
        # 原来的线程则负责持续更新UI，实现一个超时倒计时，并等待新线程的任务完成
        # #多线程请求
        self.request_thread = QThread()
        self.request_thread.start()

        # 将 self.open_ai 移动到线程并启动
        self.open_ai.moveToThread(self.request_thread)
        self.open_ai.start()

    def tools_handle_response(self, response):
        print("Starting tools_handle_response")
        self.iteration_results.append(response)
        self.last_iteration_result = response
        self.chat_dialog_body.context_history[1].append("The main idea of the previous section is?" + response)
        self.key = 1
        print("release key")

    def getPDF(self, pdf_dir):
        self.chat_dialog_body.add_message("system", f"'begin analysis on:', {pdf_dir}")
        import tiktoken
        ############################## <第 0 步，切割PDF> ##################################
        # 递归地切割PDF文件，每一块（尽量是完整的一个section，比如introduction，experiment等，必要时再进行切割）
        # 的长度必须小于 2500 个 Token
        file_content, page_one = read_and_clean_pdf_text(pdf_dir)  # （尝试）按照章节切割PDF

        TOKEN_LIMIT_PER_FRAGMENT = 2500

        from .crazy_utils import breakdown_txt_to_satisfy_token_limit_for_pdf
        enc = tiktoken.encoding_for_model(self.chat_dialog_body.config["OpenAI"]["LLM_MODEL"])
        def get_token_num(txt): return len(enc.encode(txt, disallowed_special=()))
        paper_fragments = breakdown_txt_to_satisfy_token_limit_for_pdf(
            txt=file_content,  get_token_fn=get_token_num, limit=TOKEN_LIMIT_PER_FRAGMENT)
        page_one_fragments = breakdown_txt_to_satisfy_token_limit_for_pdf(
            txt=str(page_one), get_token_fn=get_token_num, limit=TOKEN_LIMIT_PER_FRAGMENT//4)
        # 为了更好的效果，我们剥离Introduction之后的部分（如果有）
        paper_meta = page_one_fragments[0].split('introduction')[0].split(
            'Introduction')[0].split('INTRODUCTION')[0]

        ############################## <第 1 步，从摘要中提取高价值信息，放到history中> ##################################
        final_results = []
        final_results.append(paper_meta)

        ############################## <第 2 步，迭代地历遍整个文章，提取精炼信息> ##################################
        i_say_show_user = f'首先你在英文语境下通读整篇论文。'
        self.sys_prompt = "You are an English thesis expert"
        # 发送信息的模板（包括更新到对话框，发送请求以及保存到历史记录，禁用输入框）
        self.chat_dialog_body.send_message(tool=i_say_show_user, sys_prompt=self.sys_prompt)
        # add_message是只增加到聊天框，不做其他
        self.chat_dialog_body.context_history[1].append("The main idea of the previous section is?" + paper_meta)
        MAX_WORD_TOTAL = 4096
        n_fragment = len(paper_fragments)
        if n_fragment >= 20:
            print('文章极长，不能达到预期效果')
        #进行优化
        n_fragment = n_fragment
        paper_fragments = paper_fragments
        self.iteration_results = []
        self.last_iteration_result = paper_meta  # 初始值是摘要
        for i in range(n_fragment):
            while not self.key:
                time.sleep(0.01)
            self.key = 0
            NUM_OF_WORD = MAX_WORD_TOTAL // n_fragment
            i_say = f"Read this section, recapitulate the content of this section with less than {NUM_OF_WORD} words: {paper_fragments[i]}"
            i_say_show_user = f"[{i + 1}/{n_fragment}] Read this section, recapitulate the content of this section with less than {NUM_OF_WORD} words: {paper_fragments[i][:200]}"
            self.chat_dialog_body.message_received.emit("system", i_say_show_user)
            self.chat_dialog_body.open_ai.prompt_queue.put((i_say, self.chat_dialog_body.context_history, self.sys_prompt, True))

        ############################## <第 3 步，整理history> ##################################
        final_results.extend(self.iteration_results)
        final_results.append(f'接下来，你是一名专业的学术教授，利用以上信息，使用中文回答我的问题。')
        # 接下来两句话只显示在界面上，不起实际作用
        i_say_show_user = f'接下来，你是一名专业的学术教授，利用以上信息，使用中文回答我的问题。'
        gpt_say = "[Local Message] 收到。"
        self.chat_dialog_body.add_message("system",i_say_show_user)
        self.chat_dialog_body.add_message("pet",gpt_say)

        ############################## <第 4 步，设置一个token上限，防止回答时Token溢出> ##################################
        from .crazy_utils import input_clipping
        _, final_results = input_clipping("", final_results, max_token_limit=3200)
        # 注意这里的历史记录被替代了
        


    def main_pdf(self):
        # 基本信息：功能、贡献者
        self.chat_dialog_body.add_message("system","函数插件功能？\n"+\
            "理解PDF论文内容，并且将结合上下文内容，进行学术解答。函数插件贡献者: Hanzoe(it's me), binary-husky"
        )
        # 获取文件名
        pdf_dir, _ = QFileDialog.getOpenFileName(None, "Select PDF file", "", "PDF Files (*.pdf)")
        if not pdf_dir:
            return
        
        try:
            import fitz
        except:
            self.chat_dialog_body.add_message("system","解析项目: {pdf_dir}"+"\n导入软件依赖失败。使用该模块需要额外依赖，安装方法```pip install --upgrade pymupdf```。")

        # 清空历史，以免输入溢出
        self.chat_dialog_body.clear_chat_history()
        self.getPDF(pdf_dir)
