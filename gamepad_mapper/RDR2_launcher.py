# 这个脚本的功能是：运行大表哥2修改器，随后通过手柄来控制修改器：
# 当按下手柄的左侧下（十字键下）和右侧A键时，发送数字键9，以触发大表哥的风灵月影的加速功能
# 该脚本必须用管理员身份运行
from inputs import get_gamepad
import win32api
import win32con
import time
import os

# 运行“大表哥2修改器.exe”
os.startfile("E:\\Game\\Red Dead Redemption 2\\大表哥2修改器.exe")
# 运行大表哥
os.startfile(r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\red dead redemption 2.lnk")

# pyautogui可以通过pyautogui.press('num9')来发送数字键9，但是呢，不知道为什么风灵月影等软件有时认有时认不出来
# 所以直接调用windows的底层API来发送按键
def press(key_code):
    win32api.keybd_event(key_code, 0, 0, 0)  # 按下
    time.sleep(0.2)
    win32api.keybd_event(key_code, 0, win32con.KEYEVENTF_KEYUP, 0)  # 松开

left_down_pressed = False  # 十字键下
right_a_pressed = False    # A键

while True:
    try:
        events = get_gamepad()
        for event in events:
            if event.code == 'ABS_HAT0Y':  # 十字键上下
                left_down_pressed = event.state == 1  # 1为下，-1为上，0为未按
            if event.code == 'BTN_SOUTH':  # A键
                right_a_pressed = event.state == 1

            # 检查是否同时按下
            if left_down_pressed and right_a_pressed:
                press(win32con.VK_NUMPAD9)
                print("已发送数字9")
                left_down_pressed = False
                right_a_pressed = False
                break
    except Exception as e: # 在手柄断开时仍能正常工作不退出
        print(f"发生错误: {e}")