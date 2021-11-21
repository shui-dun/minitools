import zipfile as zf
import time

def decompression(passwd):
    try:
        file.extractall(path='.', pwd=passwd.encode('utf-8'))
        print('password: {}'.format(passwd))
        return True
    except Exception as e:
        print('{}: {}'.format(passwd, e))
        return False


if __name__ == '__main__':
    start = time.time()
    file = zf.ZipFile('hello.zip', 'r')
    with open(r'D:\file\offline\破解字典\弱口令集\wordlist.txt', encoding='gb2312') as f:
        for line in f:
            if decompression(line[:-1]):
                break
    print('花费时间: {:.3f}s'.format(time.time() - start))
