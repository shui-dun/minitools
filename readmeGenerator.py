"""
读取所有子文件夹中的readme.md文件，生成一个总的readme.md文件
"""

import os
import re


def readIndex():
    """
    读取REAME.md文件中已有的索引，例如从：

    - [haha](./haha) hello world
    - [hehe](./hehe) hello world

    读取出['haha', 'hehe']
    """
    with open('README.md', 'r', encoding='utf-8') as f:
        readme = f.read()
    # 转化为列表，格式为：[(subFolder, description), ...]
    index = re.findall(r'- \[(.*)\]', readme)
    return index

def readSubReadme():
    """
    读取当前文件夹子文件夹中的readme.md文件，将第一行不是标题或空行的内容作为项目简介
    返回一个列表，格式为：[(subFolder, description), ...]
    """
    # 获取当前文件夹下的所有子文件夹
    subFolders = os.listdir()
    subReadme = dict()
    for subFolder in subFolders:
        # 如果不是文件夹，跳过
        if not os.path.isdir(subFolder):
            continue
        # 判断是否有readme.md文件
        if not os.path.exists(subFolder + '/README.md'):
            continue
        # 读取readme.md文件，读取第一行不是标题或空行的内容，作为项目简介
        with open(subFolder + '/README.md', 'r', encoding='utf-8') as f:
            readme = f.read()
        description = re.findall(r'^(?!#)(.+)', readme, re.M)[0]
        subReadme[subFolder] = description
    return subReadme

def writeNewReadme():
    """
    将新的索引写入README.md文件
    """
    # 读取已有的项目名称
    index = readIndex()
    # 读取子文件夹中的readme.md文件
    subReadme = readSubReadme()
    # 设置写入项目顺序，先写入已有的项目，再写入新的项目
    sortedSubReadme = []
    for subFolder in index:
        sortedSubReadme.append((subFolder, subReadme[subFolder]))
        del subReadme[subFolder]
    for subFolder, description in subReadme.items():
        sortedSubReadme.append((subFolder, description))
    # 将新的索引写入README.md文件
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write('# minitools\n\n迷你工具，不想一个个单独做成仓库，于是放在了一起\n\n')
        for subFolder, description in sortedSubReadme:
            f.write(f'- [{subFolder}](./{subFolder}) {description}\n')

if __name__ == '__main__':
    writeNewReadme()