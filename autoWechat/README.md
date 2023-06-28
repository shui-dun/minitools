# autoWechat

微信自动发消息

## 使用方法

- 安装依赖：`pip install pyautogui pyperclip pygetwindow`
- 按照 `msg.template.json` 编写 `msg.json`
- 登录微信
- 运行 `python main.py`

## 打包方法

如果目标电脑没有python环境，可以打包

```python
# 建立虚拟环境（如果不建立新环境，打包时会包含很多不需要的包）
pip install pipenv
pipenv install
# 进入虚拟环境
pipenv shell
# 安装模块
pip install pyautogui pyperclip pygetwindow
# 打包的模块也要安装
pip install pyinstaller
# 设置编码，否则读取文件会有编码问题
chcp 65001
# 开始打包
pyinstaller -Fw main.py
```

## 消息生成

如果不知道该写什么消息，可以使用以下prompt询问chatGPT：

> 请你扮演一个中国人，为我编写10条端午节祝福短信，简洁一点，口语化一些

