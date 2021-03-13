import pyperclip
import json

# 将http消息头转化为python字典
# 从剪切板读入http消息头，将结果写入剪切板

if __name__ == '__main__':
    d = dict()
    for l in pyperclip.paste().splitlines():
        pair = l.split(':', maxsplit=1)
        d[pair[0]] = pair[1].strip()
    pyperclip.copy(json.dumps(d, indent=4))
