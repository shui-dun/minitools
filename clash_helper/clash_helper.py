import requests
import random

url = 'http://127.0.0.1:60561/proxies/GLOBAL'
lst = []


# 使用clash的restful API，实现代理手动切换

def get_proxies_list():
    """
    获取所有可用代理，存于lst中,该函数会被switch_proxy调用，无需手动调用
    """
    global lst
    proxies = requests.get(url)
    jsn = proxies.json()
    lst = jsn['all'][2:-3]


def switch_proxy():
    """
    打开clash后调用该函数即可实现随机切换全局的代理
    """
    if len(lst) == 0:
        get_proxies_list()
    proxy = random.choice(lst)
    data = '{{"name": "{}"}}'.format(proxy).encode('utf-8')
    requests.put(url, data=data)
