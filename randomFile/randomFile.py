import numpy as np

# 生成随机的文件

if __name__ == '__main__':
    fileName = input('请输入文件名: ')
    size = int(input('请输入文件大小: '))
    content = np.random.bytes(size)
    with open(fileName, 'wb') as f:
        f.write(bytes(content))
