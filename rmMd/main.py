import pyperclip
import re
import os
from urllib.parse import unquote

if __name__ == '__main__':
    # 从剪切板读取markdown文件的路径
    mdPath = pyperclip.paste().strip('"')
    # 该markdown文件所引用的所有图片所在的所有文件夹
    imgFolders = set()
    # 该markdown文件所在的目录
    rootPath = os.path.dirname(mdPath)
    with open(mdPath, encoding="utf8") as f:
        mdContent = f.read()
    # 读取所有引用的图片路径
    imgPathList = re.findall(r'!\[.*\]\((.*)\)', mdContent)
    # unquote
    imgPathList = [unquote(img) for img in imgPathList]
    # 过滤到那些非本地的图片
    imgPathList = list(filter(lambda x: x[:4] != "http", imgPathList))
    for img in imgPathList:
        imgFullPath = os.path.join(rootPath, img)
        # 如果图片路径有效
        if os.path.exists(imgFullPath):
            # 记录该图片所在的文件夹
            imgFolders.add(os.path.dirname(imgFullPath))
            # 删除该图片
            os.remove(imgFullPath)
    # 删除在删除图片后变为空的文件夹
    for imgFolder in imgFolders:
        if len(os.listdir(imgFolder)) == 0:
            os.removedirs(imgFolder)
    # 删除Markdown文件本身
    os.remove(mdPath)
