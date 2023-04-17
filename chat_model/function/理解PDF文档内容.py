from .crazy_utils import read_and_clean_pdf_text
import time
import threading

def send_request_in_thread(self):
    while not self.get_key:
        time.sleep(0.1)
    self.open_ai.prompt_queue.put((i_say, chat_dialog_body.context_history, sys_prompt, True))

def 解析PDF(pdf_dir, chat_dialog_body):
    #控制队列中的线程，避免一瞬间把所有请求发完，要拿到钥匙之后才能发送下一个
    get_key = True
    def tools_handle_response(response):
        #添加历史到gpt回复
        chat_dialog_body.context_history[1].append("The main idea of the previous section is?"+response)
        iteration_results.append(response)
        get_key = False

    # 用来获取api多线程完成结果（gpt的回复）的槽函数（很重要）
    chat_dialog_body.open_ai.tools_received.connect(tools_handle_response)    
    print('begin analysis on:', pdf_dir)
    import tiktoken
    ############################## <第 0 步，切割PDF> ##################################
    # 递归地切割PDF文件，每一块（尽量是完整的一个section，比如introduction，experiment等，必要时再进行切割）
    # 的长度必须小于 2500 个 Token
    file_content, page_one = read_and_clean_pdf_text(
        pdf_dir)  # （尝试）按照章节切割PDF

    TOKEN_LIMIT_PER_FRAGMENT = 2500

    from .crazy_utils import breakdown_txt_to_satisfy_token_limit_for_pdf
    enc = tiktoken.encoding_for_model(chat_dialog_body.config["OpenAI"]["LLM_MODEL"])
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
    sys_prompt = "You are an English thesis expert"
    #发送信息的模板（包括更新到对话框，发送请求以及保存到历史记录，禁用输入框）
    chat_dialog_body.send_message(tool=i_say_show_user,sys_prompt=sys_prompt)
    #add_message是只增加到聊天框，不做其他
    iteration_results = []
    last_iteration_result = paper_meta  # 初始值是摘要
    MAX_WORD_TOTAL = 4096
    n_fragment = len(paper_fragments)
    if n_fragment >= 20:
        print('文章极长，不能达到预期效果')
    for i in range(n_fragment):
        
        # 保存到历史
        # chat_dialog_body.context_history[0].append(i_say)
        # 将请求放进线程中，避免界面卡顿
        while not get_key:
            print("waitting.....")
            time.sleep(0.1)  # 等待100毫秒后再次检查
        chat_dialog_body.open_ai.prompt_queue.put((i_say, chat_dialog_body.context_history, sys_prompt,True))
        get_key = False

    ############################## <第 3 步，整理history> ##################################
    final_results.extend(iteration_results)
    final_results.append(f'接下来，你是一名专业的学术教授，利用以上信息，使用中文回答我的问题。')
    # 接下来两句话只显示在界面上，不起实际作用
    i_say_show_user = f'接下来，你是一名专业的学术教授，利用以上信息，使用中文回答我的问题。'
    chat_dialog_body.add_message("system", i_say_show_user)
    #启用输入框
    chat_dialog_body.message_input.setEnabled(True)
    chat_dialog_body.send_button.setEnabled(True)

    ############################## <第 4 步，设置一个token上限，防止回答时Token溢出> ##################################
    from .crazy_utils import input_clipping
    _, final_results = input_clipping("", final_results, max_token_limit=3200,chat_dialog_body=chat_dialog_body)
    # 注意这里的历史记录被替代了

def 理解PDF文档内容标准文件输入(chat_dialog_body):
    import glob
    import os
    # 基本信息：功能、贡献者
    chat_dialog_body.add_message("system","函数插件功能？\n"+\
        "理解PDF论文内容，并且将结合上下文内容，进行学术解答。函数插件贡献者: Hanzoe(it's me), binary-husky"
    )
    import tkinter as tk
    from tkinter import filedialog
    # 获取文件名

    pdf_dir = filedialog.askopenfilename()

    try:
        import fitz
    except:
        chat_dialog_body.add_message("system","解析项目: {pdf_dir}"+"\n导入软件依赖失败。使用该模块需要额外依赖，安装方法```pip install --upgrade pymupdf```。")

    # 清空历史，以免输入溢出
    chat_dialog_body.clear_chat_history()
    
    解析PDF(pdf_dir, chat_dialog_body)
