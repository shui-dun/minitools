import os
import re

textType = ['html', 'htm', 'css', 'js', 'scss']

if __name__ == '__main__':
    # 修改path后运行这个文件
    path = r"D:\file\code\front-end"
    for root, subDirs, files in os.walk(path):
        for file in files:
            fullName = '{}\\{}'.format(root, file)
            if file.rsplit('.', maxsplit=1)[1] in textType:
                with open(fullName, encoding='utf8') as f:
                    s = f.read()
                s = re.sub(r'https?:/', '', s)
                with open(fullName, 'w', encoding='utf8') as f:
                    f.write(s)
