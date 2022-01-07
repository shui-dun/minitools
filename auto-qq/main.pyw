import pyautogui as g
import pyperclip as c
import time
import random


def type_str(text):
    c.copy(text)
    g.hotkey('ctrl', 'v')
    time.sleep(0.5)


def random_text():
    f = open('txt.txt', encoding='utf8')
    txt = f.readlines()
    count = len(txt)
    nu = random.randint(0, count - 1)
    f.close()
    return txt[nu]


if __name__ == '__main__':
    qq_small = g.locateOnScreen('img/qq-small.png')
    if qq_small:
        g.click(g.center(qq_small), pause=0.7)
    else:
        g.doubleClick(g.locateCenterOnScreen('img/qq.png'))
        while not g.locateOnScreen('img/search.png'):
            time.sleep(1)
    type_str('huangxiaoke')
    g.click(g.locateCenterOnScreen('img/enter.png'), pause=1)
    for i in range(18):
        type_str(random_text())
        g.hotkey('ctrl', 'enter', pause=0.6)
