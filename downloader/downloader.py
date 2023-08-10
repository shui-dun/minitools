from concurrent.futures import *
import requests
import threading
import time
from contextlib import closing
import os


class Downloader:
    def __init__(self, url, nThread, proxies):
        self.session = requests.Session()
        head = self.session.head(url, proxies=proxies).headers
        self.size = int(head['Content-Length'])
        print('文件大小：{}'.format(self.size))
        self.name = url[url.rfind('/') + 1:]
        ind = self.name.find('?')
        if ind != -1:
            self.name = self.name[0:ind]
        print('文件名：{}'.format(self.name))
        self.url = url
        self.nThread = nThread
        self.proxies = proxies
        perSize = self.size // self.nThread
        self.begin = [i for i in range(0, self.size, perSize)]
        self.end = [i + perSize - 1 for i in self.begin]
        self.end[self.nThread - 1] = self.size - 1
        if not os.path.exists('download'):
            os.mkdir('download')

    # 下载子任务
    def downloadSub(self, i):
        headers = {'Range': "bytes={}-{}".format(self.begin[i], self.end[i])}
        with closing(self.session.get(self.url, headers=headers, proxies=self.proxies, stream=True)) as resp, \
                open("download/{}.{}".format(self.name, i), 'wb') as f:
            for chunk in resp.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

    # 统计当前下载进度
    def statistics(self):
        while True:
            s = 0
            for i in range(self.nThread):
                file = 'download/{}.{}'.format(self.name, i)
                if os.path.exists(file):
                    s += os.path.getsize(file)
            r = s / self.size * 100
            if r == 100:
                break
            print("\r当前进度：{}/{} {:.2f}%".format(s, self.size, r), end='')
            time.sleep(1)

    # 把多个文件合并成一个文件
    def mulToOne(self):
        with open('download/{}'.format(self.name), 'wb') as f:
            for i in range(self.nThread):
                fName = 'download/{}.{}'.format(self.name, i)
                with open(fName, 'rb') as file:
                    f.write(file.read())
                os.remove(fName)

    # 下载
    def download(self):
        tBegin = time.time()
        with ThreadPoolExecutor(max_workers=self.nThread) as pool:
            for i in range(self.nThread):
                pool.submit(self.downloadSub, i)
            self.statistics()
        self.mulToOne()
        print('\n花费时间：{:.2f}s'.format(time.time() - tBegin))


if __name__ == '__main__':
    url = input("请输入url：").rstrip()
    nThread = 48
    proxies = {'http': 'http://localhost:1081', 'https': 'http://localhost:1081'}
    downloader = Downloader(url, nThread, proxies)
    downloader.download()
