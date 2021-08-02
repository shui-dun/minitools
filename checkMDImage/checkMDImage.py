import os
import re

from urllib.parse import unquote

# 检测markdown文件中所对应的本地图片是否存在
# 并检测文件夹中的文件是否被markdown文件引用

mdList = []

auxiliaryList = []

foundList = []


def check(root, file):
    fullPath = r'{}{}{}'.format(root, os.sep, file)
    with open(fullPath, encoding='utf8') as f:
        s = f.read()
    imgPathList = re.findall(r'!\[.*\]\((.*)\)', s)
    imgPathList = [unquote(r'{}{}{}'.format(root, os.sep, img)).replace('/', os.sep) for img in imgPathList]
    global foundList
    foundList += imgPathList
    if len(imgPathList) == 0:
        return
    for img in imgPathList:
        if not os.path.isfile(img):
            print('in: [{}] img_name: [{}]'.format(fullPath, img))


def specialSuffix(file):
    lst = file.rsplit('.', maxsplit=1)
    if len(lst) == 1:
        return False
    return lst[1] in ['vsdx', 'drawio']


def traverse(path):
    for root, subDirs, files in os.walk(path):
        if '.git' in root.rsplit(os.sep):
            continue
        for file in files:
            if file[-3:] == '.md':
                mdList.append((root, file))
            else:
                fullPath = '{}{}{}'.format(root, os.sep, file)
                auxiliaryList.append(fullPath)
    for mdFile in mdList:
        try:
            check(*mdFile)
        except Exception as e:
            print(e)
    for file in auxiliaryList:
        if file not in foundList and not specialSuffix(file):
            print('not used: [{}]'.format(file))


if __name__ == '__main__':
    traverse(r"D:\file\code\notebook")
