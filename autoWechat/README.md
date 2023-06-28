# autoWechat

微信自动发消息

## 使用方法

- 安装pipenv：`pip install pipenv`
- 安装环境以及依赖：`pipenv install`
- 按照 `msg.template.json` 编写 `msg.json`
- 登录并打开微信窗口
- 运行 `pipenv run main.py`

## 打包方法

如果目标电脑没有python环境，可以打包

```python
# 设置编码，否则读取文件会有编码问题
chcp 65001
# 开始打包
pyinstaller -Fw main.py
```

## 消息生成

如果不知道该写什么消息，可以使用以下prompt询问chatGPT：

> 请你扮演一个中国人，为我编写10条端午节祝福短信，简洁一点，口语化一些

