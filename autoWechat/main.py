import json
import pyautogui as g
import pyperclip
import pygetwindow as gw
import time

if __name__ == '__main__':
    # 根据窗口标题获取窗口
    window = gw.getWindowsWithTitle("微信")[0]
    # 如果窗口被最小化了，那么先恢复
    if window.isMinimized:
        window.restore()
    # 将窗口置于最顶部
    window.activate()

    # 使用utf8编码打开json文件
    with open('msg.json', 'r', encoding='utf8') as f:
        msgs = json.load(f)
    
    pause = 0.5

    for msgGroup in msgs:
        appellations = msgGroup['appellation']
        msg = msgGroup['msg']
        for name, appellation in appellations.items():
            finalMsg = msg.replace('{}', appellation)
            g.hotkey('ctrl', 'f')
            time.sleep(pause)
            pyperclip.copy(name)
            time.sleep(pause)
            g.hotkey('ctrl', 'v')
            time.sleep(pause)
            g.hotkey('enter')
            time.sleep(pause)
            pyperclip.copy(finalMsg)
            g.hotkey('ctrl', 'v')
            time.sleep(pause)
            g.hotkey('enter')
            time.sleep(pause)
