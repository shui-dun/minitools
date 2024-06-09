import requests
from bs4 import BeautifulSoup
import time
import os
import re

pattern = r"阳历：(\d{4}年\d{1,2}月\d{1,2}日)"

festival = "chunjie"

def retry(attempts, interval):
    """重试装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            for i in range(attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f"请求失败，正在尝试第{i+1}次重试。")
                    time.sleep(interval)  # 等待一段时间后重试
            raise Exception("重试次数达到上限，任务失败。")
        return wrapper
    return decorator

@retry(attempts=3, interval=2)
def fetch_yearly_date(year):
    # 从环境变量中读取lunar_url
    lunar_url = os.getenv("LUNAR_URL")
    url = f"https://{lunar_url}/{year}-{festival}.html"
    response = requests.get(url)
    response.encoding = "utf-8"
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        # 查找包含阳历日期的节点
        div_jr_list = soup.find_all("div", {"class": "divjr"})
        if len(div_jr_list) != 1:
            print(f"ERROR: 在 {year} 年中找到了 {len(div_jr_list)} 个阳历日期，分别为：{div_jr_list}")
            return None
        div_jr = div_jr_list[0]
        date_text = div_jr.text.strip()
        # 提取日期
        match = re.search(pattern, date_text)
        if match:
            return match.group(1)  # 获取第一个捕获组的内容，即日期部分
        else:
            print(f"ERROR: 未能提取出 {year} 年的阳历日期。")
            return None
    else:
        raise Exception("无法从服务器获取数据。")

def load_existing_dates(filename):
    if not os.path.exists(filename):
        return dict()
    dates = dict()
    with open(filename, 'r', encoding='utf-8') as file:
        for line in file:
            # 获得年份，即“年”之前的部分
            year = line.split("年")[0]
            dates[year] = line.strip()
    return dates

def save_date(filename, date):
    with open(filename, 'a', encoding='utf-8') as file:
        file.write(date + '\n')

# 加载已存在的日期
cached_dates = load_existing_dates(f"{festival}.txt")

# 获取并保存日期
for year in range(2024, 2100):
    if str(year) in cached_dates:
        print(f"{year} 年的日期已存在，跳过。")
        continue
    date = fetch_yearly_date(year)
    time.sleep(1)  # 休息一下，避免给服务器太大压力
    if date:
        save_date(f"{festival}.txt", date)
        print(f"已成功获取并写入 {year} 的日期：{date}")


print(f"所有日期已成功保存到文件 {festival}.txt。")
