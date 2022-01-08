from isFullScreen import is_full_screen
import time
import pyautogui
import random

if __name__ == '__main__':
    while True:
        time.sleep(60)
        if is_full_screen():
            pyautogui.hotkey('shift', 'ctrl', 'alt', ']')
