from .crazy_utils import read_and_clean_pdf_text

def 解析PDF(pdf_dir, chat_dialog_body):
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
    gpt_say = "[Local Message] 收到。"           # 用户提示
    chat_dialog_body.append_message([i_say_show_user, gpt_say])

    iteration_results = []
    last_iteration_result = paper_meta  # 初始值是摘要
    MAX_WORD_TOTAL = 4096
    n_fragment = len(paper_fragments)
    if n_fragment >= 20:
        print('文章极长，不能达到预期效果')
    for i in range(n_fragment):
        NUM_OF_WORD = MAX_WORD_TOTAL // n_fragment
        i_say = f"Read this section, recapitulate the content of this section with less than {NUM_OF_WORD} words: {paper_fragments[i]}"
        i_say_show_user = f"[{i+1}/{n_fragment}] Read this section, recapitulate the content of this section with less than {NUM_OF_WORD} words: {paper_fragments[i][:200]}"
        iteration_results.append(gpt_say)
        last_iteration_result = gpt_say
        chat_dialog_body.append_message(message=f'我:{i_say_show_user}',is_user=True)
        # 更新聊天上下文
        chat_dialog_body.context_history += f"user: {i_say}\n"
        prompt = i_say
        chat_dialog_body.open_ai.prompt_queue.put((prompt, chat_dialog_body.context_history))  # 将聊天上下文作为第二个参数传递
        chat_dialog_body.message_input.clear()

        # 保存聊天记录到本地
        chat_dialog_body.save_chat_history()

    ############################## <第 3 步，整理history> ##################################
    final_results.extend(iteration_results)
    final_results.append(f'接下来，你是一名专业的学术教授，利用以上信息，使用中文回答我的问题。')
    # 接下来两句话只显示在界面上，不起实际作用
    i_say_show_user = f'接下来，你是一名专业的学术教授，利用以上信息，使用中文回答我的问题。'
    gpt_say = "[Local Message] 收到。"
    chat_dialog_body.append_message([i_say_show_user, gpt_say])

    ############################## <第 4 步，设置一个token上限，防止回答时Token溢出> ##################################
    from .crazy_utils import input_clipping
    _, final_results = input_clipping("", final_results, max_token_limit=3200,chat_dialog_body=chat_dialog_body)
    # 注意这里的历史记录被替代了

def 理解PDF文档内容标准文件输入(chat_dialog_body):
    import glob
    import os
    # 基本信息：功能、贡献者
    chat_dialog_body.append_message([
        "函数插件功能？",
        "理解PDF论文内容，并且将结合上下文内容，进行学术解答。函数插件贡献者: Hanzoe(it's me), binary-husky"])
    import tkinter as tk
    from tkinter import filedialog
    # 获取文件名

    pdf_dir = filedialog.askopenfilename()

    try:
        import fitz
    except:
        chat_dialog_body.append_message("解析项目: {pdf_dir}"+"\n导入软件依赖失败。使用该模块需要额外依赖，安装方法```pip install --upgrade pymupdf```。")

    # 清空历史，以免输入溢出
    chat_dialog_body.clear_chat_history()
    
    解析PDF(pdf_dir, chat_dialog_body)
