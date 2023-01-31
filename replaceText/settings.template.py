import re

# 目录位置
path = r"C:\path"

# 合法格式
suffix = [".md", ".txt"]

# 被替换的字符串
origin = r"origin"

# 替换成的字符串，支持lambda表达式
dest = "dest"

# re的模式
flags = 0

# 替换次数，0代表替换所有
count = 0

# 要忽略的文件夹
ignoredFolders = ['a']