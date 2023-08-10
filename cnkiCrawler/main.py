import os

from selenium.common.exceptions import ElementNotInteractableException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time


def info(driver):
    # 得到摘要
    try:
        button = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#ChDivSummaryMore"))
        )
    except TimeoutException as e:
        return 'error'
    try:
        driver.execute_script("arguments[0].scrollIntoView(true);", button)
        button.click()
    except ElementNotInteractableException as e:
        pass
    abstract = driver.find_element_by_css_selector(".wxBaseinfo p")
    # 得到标题
    title = driver.find_element_by_css_selector(".wxTitle h2.title")
    # 得到作者
    authors = driver.find_element_by_css_selector(".author")
    # 得到期刊名称
    publication = driver.find_element_by_css_selector(".sourinfo .title")
    # 得到年份
    year = driver.find_element_by_css_selector(".sourinfo>p+p+p")
    return title.text, authors.text, publication.text, year.text, abstract.text


def crawler(driver: webdriver.Chrome, keyword, nPages):
    # 创建文件
    outputFile = "data/{}.txt".format(keyword)
    if not os.path.exists(outputFile):
        with open(outputFile, 'w') as f:
            pass
    # 进入网页
    url = r'https://chkdx.cnki.net/KNS/Brief/singleResult.aspx?code=CHKJ&kw={}'.format(keyword)
    driver.get(url)
    # 手动调整起始页数
    input()
    # 进入iframe
    iframe = WebDriverWait(driver, 3).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#iframeResult"))
    )
    driver.switch_to.frame(iframe)
    # 对于每一页
    for _ in range(nPages):
        nPaper = 0
        while True:
            # 等待
            time.sleep(1.5)
            # 找到指定条目
            paperTable = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".GridTableContent"))
            )
            links = paperTable.find_elements_by_css_selector("a.fz14")
            # 如果本页访问完，点击下一页
            if nPaper >= len(links):
                buttonTable = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".pageBar_bottom"))
                )
                nextPageButton = buttonTable.find_elements_by_css_selector("a")[-1]
                nextPageButton.click()
                break
            curLink = links[nPaper]
            nPaper += 1
            # 切换窗口
            windowBefore = driver.window_handles[0]
            curLink.click()
            windowAfter = driver.window_handles[1]
            driver.switch_to.window(windowAfter)
            # 写入文件
            metadata = info(driver)
            with open(outputFile, 'a') as f:
                f.write("{}\n".format(metadata))
            driver.close()
            # 切换回窗口
            driver.switch_to.window(windowBefore)
            # 进入iframe
            iframe = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#iframeResult"))
            )
            driver.switch_to.frame(iframe)


if __name__ == '__main__':
    chrome_options = Options()
    # chrome_options.add_argument('--headless')
    driver = webdriver.Chrome(options=chrome_options)
    crawler(driver, '肺癌', 10)
    driver.quit()
