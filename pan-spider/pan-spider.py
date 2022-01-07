from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
import requests
from bs4 import BeautifulSoup
import threading
from urllib.parse import urlsplit
from user_agent_list import random_headers


class PanSpider:
    def __init__(self, keyword):
        self.keyword = keyword

    def run(self):
        for url in self.get_urls_from_bing():
            threading.Thread(target=self.bfs, args=(url,)).start()

    def get_urls_from_bing(self):
        search_urls = set()
        browser = webdriver.Edge()
        browser.get('https://cn.bing.com/')
        WebDriverWait(browser, 10).until(lambda driver: driver.find_element_by_id('sb_form_q'))
        browser.find_element_by_id('sb_form_q').send_keys(self.keyword + ' 百度网盘' + Keys.ENTER)
        for _ in range(2):
            WebDriverWait(browser, 10).until(lambda driver: driver.find_element_by_xpath('//a[@title="下一页"]'))
            for a in browser.find_elements_by_xpath('//a[@target="_blank"]'):
                if a.find_element_by_xpath("./..").tag_name == 'h2':
                    search_urls.add(a.get_attribute('href'))
            browser.find_element_by_xpath('//a[@title="下一页"]').click()
        browser.quit()
        return search_urls

    def bfs(self, url):
        urls = {url, }
        visited = set()
        for _ in range(150):
            if len(urls) == 0:
                break
            link = urls.pop()
            if link in visited:
                continue
            visited.add(link)
            print('开始搜索{}'.format(link))
            urls.update(self.get_links_from_current_link(link))

    def pan_has_content(self, link):
        try:
            response = requests.get(link, headers=random_headers())
            response.encoding = 'utf8'
            if '永久有效' in response.text:
                return True
        except Exception as e:
            pass
        return False

    def check_pan(self, link):
        if 'pan.baidu.com' in link or 'yun.baidu.com' in link:
            if self.pan_has_content(link):
                print('***** 找到资源 *****：{}'.format(link))
                with open(self.keyword + '.txt', 'a') as f:
                    f.write('{}\n'.format(link))
            return True
        return False

    def get_links_from_current_link(self, url):
        links = set()
        try:
            response = requests.get(url, headers=random_headers())
            response.encoding = 'utf8'
            soup = BeautifulSoup(response.text, 'html.parser')
            for a in soup.find_all('a'):
                link = a['href']
                if not self.check_pan(link):
                    text = str(a)
                    if self.keyword.lower() in text.lower() or '百度网盘' in text or '百度云' in text:
                        if link[:4] == 'http':
                            pass
                        elif link[:2] == '//':
                            link = 'http:{}'.format(link)
                        else:
                            split_url = urlsplit(url)
                            link = '{}://{}{}'.format(split_url.scheme, split_url.netloc, link)
                        links.add(link)
        except Exception as e:
            pass
        return links


if __name__ == '__main__':
    keyword = input('请输入想要查找的资源：')
    spider = PanSpider(keyword)
    spider.run()
