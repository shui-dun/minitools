from selenium import webdriver
import time
from selenium.webdriver.common.keys import Keys
import pyautogui
import pyperclip
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = webdriver.Chrome()

# 将网页转化为pdf，写入
def write(name):
    pyautogui.hotkey('ctrl', 'p')
    time.sleep(5)
    pyautogui.press('enter')
    time.sleep(2)
    pyperclip.copy('{}.pdf'.format(name))
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(2)
    pyautogui.press('enter')
    time.sleep(2)


# 跳转到下一页
def nextPage():
    elements = driver.find_elements_by_class_name("orientationright")
    button = None
    for element in elements:
        if element.value_of_css_property('display') == 'block':
            button = element
    button.click()


# 得到当前页的名称
def get_name():
    element1 = driver.find_element_by_xpath("//h1").text
    try:
        element2 = driver.find_element_by_xpath("//span[contains(@class,'currents')]").get_attribute('title')
    except Exception as e:
        element2 = ''
    ans = '{}---{}'.format(element1, element2)
    print(ans)
    return ans

# 等待
def wait():
    element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "orientationright"))
    )
    time.sleep(8)


if __name__ == '__main__':
    driver.maximize_window()
    driver.get(
        "https://mooc1-1.chaoxing.com/mycourse/studentstudy?chapterId=228489488&courseId=205570038&clazzid=38533218&enc=da069b8b2cf79a779762628a5276e7f3")
    input()
    time.sleep(2)
    while True:
        try:
            wait()
            write(get_name())
            nextPage()
        except Exception as e:
            print(e)
