import os
import re
import requests
from urllib.parse import quote

session = requests.session()


def localize(root, file):
    fullPath = r'{}{}{}'.format(root, os.sep, file)
    with open(fullPath, encoding='utf8') as f:
        s = f.read()
    imgPathList = re.findall(r'!\[.*\]\((https?:\/\/.*)\)', s)
    if len(imgPathList) == 0:
        return
    imgNameList = [path.rsplit('/', maxsplit=1)[1] for path in imgPathList]
    originFolder = '.{}'.format(file[:-3])
    fullFolder = '{}{}{}'.format(root, os.sep, originFolder)
    quoteFolder = quote(originFolder)
    if not os.path.exists(fullFolder):
        os.makedirs(fullFolder)
    for imgName, imgPath in zip(imgNameList, imgPathList):
        s = re.sub(imgPath, r'{}/{}'.format(quoteFolder, imgName), s)
        content = session.get(imgPath).content
        with open(r'{}{}{}'.format(fullFolder, os.sep, imgName), 'wb') as f:
            f.write(content)
    with open(fullPath, 'w', encoding='utf8') as f:
        f.write(s)


def traverse(path):
    for root, subDirs, files in os.walk(path):
        for file in files:
            if file[-3:] == '.md':
                try:
                    localize(root, file)
                except Exception as e:
                    print(e)


if __name__ == '__main__':
    traverse(r"C:\Users\26046\Desktop\notebook")
