from settings import files
import os
import sys

# 第一个参数是终点文件夹
dest = sys.argv[1]
print(dest)

# 对于files里面的每一个文件
for file in files:
    # 得到文件名
    filename = os.path.basename(file)
    print(filename)
    # 得到新的文件名
    newFilename = os.path.join(dest, filename)
    # 创建符号链接
    os.symlink(file, newFilename)