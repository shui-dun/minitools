import re
import os

# path = r'D:\file\cloud\notebook' # 目录位置
path = r'C:\Users\26046\Desktop'
suffix = ['.md'] # 合法格式

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
                # s = re.sub(r'\n', r' ', s)
                # 必须用二进制形式打开，不然会改变换行符
                with open(fullName, 'wb') as f:
                    f.write(bytes(s,  encoding = "utf8"))
