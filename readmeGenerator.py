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
    index = re.findall(r'- \[(.*?)\]', readme)
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
    
    # 设置写入项目顺序，先写入新的项目，再写入已有的项目
    sortedSubReadme = []
    
    # 先加入新的项目
    for subFolder, description in subReadme.items():
        if subFolder not in index:
            sortedSubReadme.append((subFolder, description))
    
    # 然后加入已有的项目
    for subFolder in index:
        if subFolder in subReadme:
            sortedSubReadme.append((subFolder, subReadme[subFolder]))

    # 将新的索引写入README.md文件
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write('# 迷你工具箱\n\n一系列迷你工具，不想一个个单独做成仓库，于是放在了一起\n\n## 工具列表\n\n')
        for subFolder, description in sortedSubReadme:
            f.write(f'- [{subFolder}](./{subFolder}) {description}\n')
        f.write('\n## hooks\n\n你可以将 [.githooks](.githooks) 软链接到 `.git/hooks`，以实现 `pre-commit` 时自动更新README\n\n## License\n\n[MIT](./LICENSE)')


if __name__ == '__main__':
    writeNewReadme()