import re
import os
import json

path = ""  # 目录位置
suffix = []  # 合法格式
origin = ""  # 被替换的字符串
dest = ""  # 替换成的字符串


def testSuffix(name):
    for s in suffix:
        if name[-len(s):] == s:
            return True
    return False


def readConfig():
    global path, suffix, origin, dest
    with open("config.json", encoding="utf8") as f:
        js = json.load(f)
    path = js["path"]
    suffix = js["suffix"]
    origin = js["origin"]
    dest = js["dest"]


if __name__ == "__main__":
    readConfig()
    for root, subDirs, files in os.walk(path):
        for file in files:
            fullName = r'{}\{}'.format(root, file)
            if testSuffix(fullName):
                with open(fullName, encoding='utf8') as f:
                    s = f.read()
                s = re.sub(origin, dest, s)
                # 必须用二进制形式打开，不然会改变换行符
                with open(fullName, 'wb') as f:
                    f.write(bytes(s, encoding="utf8"))
