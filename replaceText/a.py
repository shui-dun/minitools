import re
import os

path = r'D:\file\cloud\notebook' # 目录位置
suffix = ['.md'] # 合法格式
fromText = r'review #review' # 要替换的文本
toText = 'tags: [ review' # 替换成什么

def testSuffix(name):
    for s in suffix:
        if name[-len(s):] == s:
            return True
    return False


if __name__ == "__main__":

    for root, subDirs, files in os.walk(path):
        for file in files:
            fullName = r'{}\{}'.format(root, file)
            if testSuffix(fullName):
                with open(fullName, encoding='utf8') as f:
                    s = f.read()
                s = re.sub(fromText, toText, s)
                with open(fullName, 'w', encoding='utf8') as f:
                    f.write(s)
