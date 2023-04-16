# Pet-GPT

![Language](https://img.shields.io/badge/language-python-brightgreen)  

Pet-GPT 是一个使用 PyQt 编写的桌面宠物程序，支持调用 OpenAI 的 GPT 进行上下文对话，然后主动找你聊天！

<div>
  <img src="https://user-images.githubusercontent.com/46673445/232178202-3e4a7558-be9a-4708-b6e4-a8baff0080af.png" alt="dog" width="200" style="display: inline-block;">
  <img src="https://user-images.githubusercontent.com/46673445/232195799-c33cfe5c-1dd5-49bb-bc2e-bdc66a61859f.png" alt="cat" width="200" style="display: inline-block;">
  <img src="https://user-images.githubusercontent.com/46673445/232278236-d8665b48-74d9-4103-8cd1-7e7411bf362b.gif" alt="basheng" width="200" style="display: inline-block;">
</div>

bilibili连接
https://www.bilibili.com/video/BV1xM4y1y7e7/?vd_source=0256cdccbe38c132828c06c0c3d6dd4f

## 特点

- 一个简单的桌面小宠物，支持自定义图像和昵称
- 支持自由移动和随机主动发问（通过gpt）等多种设置
- 使用 OpenAI GPT 进行上下文的单词对话
- 支持聊天界面的自定义插件热更新
- 能延续QQ宠物的梦

## 目前的功能
功能 | 描述
--- | ---
主动对话v1 | 使用模板随机发起对话，不再被动聊天（下一版本，先向gpt获取对话内容，再主动对话，更生动）
英文润色 | 修改源语言为专业的英语
python解释器 | 模拟python，直接执行命令
自定义插件 | 支持开发设计自己的插件
配置代理服务器 | 支持配置代理服务器
模块化设计 | 支持自定义高阶的实验性功能与相关代码
更换宠物图像 | 选择自己喜欢的图像作为展示（虚拟人物、动物都OK）
…… | ……

## 安装与运行

1. 安装 Python 3.9 及以上版本和 PyQt5。

2. 在 OpenAI 上注册账号，并获取 API 密钥。

   在浏览器中打开 https://beta.openai.com/signup/，填写相关信息注册 OpenAI 账号，并获取 API 密钥。

3. 克隆或下载本项目。

   - 点击绿色的“Code”按钮，选择“Download ZIP”
   - 使用git命令`git clone https://github.com/Hanzoe/petgpt.git`下载。

4. 将`config.ini`修改为`private_config.ini` ，并且修改参数"OPENAI_API_KEY"、"LLM_MODEL"。
   - 有代理的话，一定要修改自己的代理地址

5. 安装依赖包

   ```
   conda create --name petgpt python=3.9
   conda activate petgpt
   pip install -r requirements.txt
   ```

   

6. 运行 `main.py`。

   ```
   python main.py
   ```

## 使用说明

- 无互动状态下，宠物自由移动、对话

  ![image](https://user-images.githubusercontent.com/46673445/232179367-46acb6c8-4eaf-45e5-86a2-fd92c1ef2fd3.png)
  ![image](https://user-images.githubusercontent.com/46673445/232290290-11e1233f-bc83-4a74-9beb-37dbf89944d8.png)


- 右键支持功能：打开聊天框、修改昵称、修改图像、设置移动以及对话

  ![image](https://user-images.githubusercontent.com/46673445/232179374-458f6fd5-85d3-41ee-889e-28b98174b240.png)
  ![image](https://user-images.githubusercontent.com/46673445/232290378-ac8f5aaf-41bc-4668-a461-bdb1f81d16c4.png)


- 互动状态下，可实现基于GPT的聊天以及其他功能
  ![image](https://user-images.githubusercontent.com/46673445/232196578-0db60c9b-594a-486d-8918-634df3dacd6b.png)
  ![image](https://user-images.githubusercontent.com/46673445/232290314-5dd7b082-3ec4-4797-8261-01e310ccabc8.png)


## 自定义插件说明
### 常规按钮格式
1. 在chatdialog.py文件找到初始化函数
   image.png
2. 按照模板添加槽
3. 定义函数
   image.png

### 下拉列表插件格式
1. 在chatdialog.py文件找到初始化函数
   - self.custom_dropdown
   image.png
2. 去self.full_slot中定义该选项

## 开发日志

### v4
- [ ] 优化界面
- [ ] 增加一些互动效果
- [ ] 聊天界面的语音输入输出
- [ ] 聊天界面的图片生成
- [ ] 请求太频繁，需要做限制
- [ ] 不定时的请求对话：要先请求到gpt，再请求到本地（重要）
- [ ] 喂食？
- [ ] 好感度？
- [ ] 跨设备平台？（重要）
- [ ] 扮演角色类使用专门的命令调用，节省页面空间

### v3
- [x] 左侧加入插件栏
- [ ] 实现宠物的互动
- [ ] 数据过大时的分批请求
- [ ] 热插件-论文阅读
- [x] 热插件-python编译器
- [x] 聊天界面的角色扮演
- [x] 解决输入框不能回车的问题
- [x] 解决解析文本框的代码
- [x] 支持gif
- [x] 支持改大小
- [x] 修改读取方式，支持中文

### v2
- [x] 按下esc时，程序崩溃
- [x] random_chat开启时，会阻碍打字
- [x] 打开聊天框时，宠物隐藏；关闭时，宠物出现
- [x] 保存对话记录，实现联系上下文进行对话


### v1
- [x] 上下文对话
- [x] 通过设置修改宠物的移动、和主动发问
- [x] 完成无记忆的一次性对话
- [x] 完成整个框架（展示，基本聊天）


## 贡献者


## 联系方式

一个人也许走的很快，但是一群人可以走得更远！

![image](https://user-images.githubusercontent.com/46673445/232263608-c2f4982f-292e-41bd-b646-96a1140f22ee.png)

## 参考
1. https://github.com/f/awesome-chatgpt-prompts（获取prompts命令）
2. https://github.com/tommyli3318/desktop-pet（想做桌面宠物版的）
3. https://github.com/binary-husky/chatgpt_academic（曾经在这上面做插件奉献，从而得到灵感）
4. https://gitee.com/fg_slash/yuanshen-desktoppet#https://gitee.com/link?target=https%3A%2F%2Fpan.baidu.com%2Fs%2F1AuUjMnYgNScTla7yQA19Og（参考了gif图）

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Hanzoe/Pet-GPT&type=Date)](https://star-history.com/#Hanzoe/Pet-GPT&Date)
