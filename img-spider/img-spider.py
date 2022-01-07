import requests
import os
import re
import time
import threading
from user_agent_list import random_headers

N_LOSE, N_SUCCESS = 0, 0


def get_link(keyword, sum):
    print('正在获取图片链接列表……')
    pn = 0
    links = set()
    while True:
        url = "https://image.baidu.com/search/flip?tn=baiduimage&ie=utf-8&word={}&pn={}" \
              "&gsm=78&ct=&ic=0&lm=-1&width=0&height=0".format(keyword, pn)
        response = requests.get(url, headers=random_headers())
        response.encoding = 'utf8'
        urls = re.findall('"objURL":"(.*?)"', response.text)
        links.update(urls)
        pn += len(urls)
        if len(links) >= sum:
            print('成功获取图片链接列表')
            return list(links)[:sum]


def download_img(link, out_path):
    img_name = link.rsplit('/', maxsplit=1)[-1]
    print('开始下载{}'.format(link))
    try:
        response = requests.get(link, random_headers())
        with open(out_path + img_name, 'wb') as f:
            f.write(response.content)
        print('{}下载成功'.format(img_name))
        # lock.acquire()
        global N_SUCCESS
        N_SUCCESS += 1
        # lock.release()
    except Exception as e:
        print('{}下载失败，发生异常：{}'.format(img_name, e))
        # lock.acquire()
        global N_LOSE
        N_LOSE += 1
        # lock.release()


if __name__ == '__main__':
    keyword = input('请输入搜索关键字：').replace(' ', '+')
    sum = int(input('请输入所需图片数目：'))
    out_path = input('请输入图片输出路径：').rstrip('\\') + '\\'
    start = time.time()
    if not os.path.exists(out_path):
        os.mkdir(out_path)
    links = get_link(keyword, sum)
    for link in links:
        threading.Thread(target=download_img, args=(link, out_path)).start()
    while len(threading.enumerate()) != 1:
        time.sleep(1)
    input('下载完成！总耗时%.3f秒，成功%d个，失败%d个，任意键继续' % (time.time() - start, N_SUCCESS, N_LOSE))
