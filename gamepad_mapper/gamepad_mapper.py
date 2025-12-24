# 该脚本通过手柄来触发键鼠按键以控制修改器
# 该脚本必须用管理员身份运行
from inputs import get_gamepad
import win32api
import win32con
import time

def press_keyboard():
    # 按下 Alt
    win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
    time.sleep(0.05)
    # 按下 8
    win32api.keybd_event(win32con.VK_NUMPAD8, 0, 0, 0)
    time.sleep(0.2)
    # 松开 8
    win32api.keybd_event(win32con.VK_NUMPAD8, 0, win32con.KEYEVENTF_KEYUP, 0)
    time.sleep(0.05)
    # 按下 9
    win32api.keybd_event(win32con.VK_NUMPAD9, 0, 0, 0)
    time.sleep(0.2)
    # 松开 9
    win32api.keybd_event(win32con.VK_NUMPAD9, 0, win32con.KEYEVENTF_KEYUP, 0)
    # 松开 Alt
    win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)

gamepad_key1_pressed = False
gamepad_key2_pressed = False

while True:
    try:
        events = get_gamepad()
        for event in events:
            if event.code == 'ABS_HAT0Y':  # 十字键上下
                gamepad_key1_pressed = event.state == -1  # 1为下，-1为上，0为未按
            if event.code == 'BTN_WEST':  # X
                gamepad_key2_pressed = event.state == 1  # 1为按下，0为未按

            # 检查是否同时按下
            if gamepad_key1_pressed and gamepad_key2_pressed:
                press_keyboard()
                print("已发送键盘按键")
                gamepad_key1_pressed = False
                gamepad_key2_pressed = False
                break
    except Exception as e: # 在手柄断开时仍能正常工作不退出
        print(f"发生错误: {e}")