import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from read import finalResult

if __name__ == '__main__':
    resultLst = finalResult()
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    driver = webdriver.Chrome(options=chrome_options)
    for word in resultLst:
        try:
            print('start: {}'.format(word))
            driver.get('https://cn.bing.com/dict/search?q={}'.format(word))
            ul = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".qdef ul"))
            )
            trans = ul.text.replace('\n', '\t')
            print(trans)
            with open('data/result.txt', 'a') as f:
                f.write('{}\t{}\n'.format(word, trans))
            time.sleep(0.8)
        except Exception as e:
            print(e)
    driver.close()
