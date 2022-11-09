import re
import os
from settings import *
import traceback


def testSuffix(name):
    for s in suffix:
        if name[-len(s):] == s:
            return True
    return False


if __name__ == "__main__":
    for root, subDirs, files in os.walk(path):
        if os.path.basename(root) in ignoredFolders:
            # dir = []并没有改变原来的列表，而dir[:] = []则是原地修改列表
            subDirs[:] = []
            continue
        for file in files:
            fullName = r'{}\{}'.format(root, file)
            if testSuffix(fullName):
                try:
                    with open(fullName, encoding='utf8') as f:
                        s = f.read()
                    sNew = re.sub(origin, dest, s, count)
                    if sNew != s:
                        print(fullName)
                        # 必须用二进制形式打开，不然会改变换行符
                        with open(fullName, 'wb') as f:
                            f.write(bytes(sNew, encoding="utf8"))
                except Exception as e:
                    print('in file: {}\t{}'.format(fullName, traceback.format_exc()))
