import re
import os

path = r'D:\file\ziliao\notebook'
suffix = ['.md']


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
                s = re.sub(r'http://pic\.shuidun\.xyz', r'http://img.testen.top', s)
                with open(fullName, 'w', encoding='utf8') as f:
                    f.write(s)
