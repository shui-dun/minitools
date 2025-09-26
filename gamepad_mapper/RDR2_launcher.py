# 这个脚本的功能是：运行大表哥修改器，随后通过手柄来控制修改器：
# 当按下手柄的LB和RB键时，发送数字键9，以触发大表哥的风灵月影的加速功能
# 该脚本必须用管理员身份运行
from inputs import get_gamepad
import win32api
import win32con
import time
import os

# 运行“大表哥2修改器.exe”
os.startfile("F:\\桌面\\游戏\\RDR2\\大表哥2修改器.exe")

# pyautogui可以通过pyautogui.press('num9')来发送数字键9，但是呢，不知道为什么风灵月影等软件有时认有时认不出来
# 所以直接调用windows的底层API来发送按键
def press(key_code):
    win32api.keybd_event(key_code, 0, 0, 0)  # 按下
    time.sleep(0.2)
    win32api.keybd_event(key_code, 0, win32con.KEYEVENTF_KEYUP, 0)  # 松开

lb_pressed = False
rb_pressed = False

while True:
    events = get_gamepad()
    for event in events:
        if event.code == 'BTN_TL':  # LB
            lb_pressed = event.state == 1 # event.state为1表示按下
        if event.code == 'BTN_TR':  # RB
            rb_pressed = event.state == 1
        # 检查是否同时按下
        if lb_pressed and rb_pressed:
            press(win32con.VK_NUMPAD9)
            print("已发送数字9")
            lb_pressed = False
            rb_pressed = False
            break
