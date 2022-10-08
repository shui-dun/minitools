from isFullScreen import isFullScreen
import time
import pyautogui

# 禁用FAILSAFE
pyautogui.FAILSAFE = False

if __name__ == '__main__':
    while True:
        time.sleep(60)
        if isFullScreen():
            pyautogui.hotkey('shift', 'ctrl', 'alt', '.')
            print("detect full screen")
