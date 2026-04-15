import time
import win32api
import win32con
import os

# 主键盘区按键码
VK_TAB = win32con.VK_TAB
VK_CONTROL = win32con.VK_CONTROL
VK_A = 0x41
VK_0 = 0x30
VK_7 = 0x37
VK_OEM_PERIOD = 0xBE  # '.'主键盘区

# 小键盘区按键码
VK_NUMPAD0 = win32con.VK_NUMPAD0
VK_NUMPAD1 = win32con.VK_NUMPAD1
VK_NUMPAD2 = win32con.VK_NUMPAD2
VK_NUMPAD7 = win32con.VK_NUMPAD7
VK_NUMPAD_ADD = win32con.VK_ADD
VK_NUMPAD_DECIMAL = win32con.VK_DECIMAL

def press_key(vk, hold=0.1):
	win32api.keybd_event(vk, 0, 0, 0)
	time.sleep(hold)
	win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)
	time.sleep(0.1)

def press_ctrl_a():
	win32api.keybd_event(VK_CONTROL, 0, 0, 0)
	win32api.keybd_event(VK_A, 0, 0, 0)
	time.sleep(0.1)
	win32api.keybd_event(VK_A, 0, win32con.KEYEVENTF_KEYUP, 0)
	win32api.keybd_event(VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
	time.sleep(0.1)

def input_main_keyboard_07():
	press_key(VK_0)
	press_key(VK_OEM_PERIOD)
	press_key(VK_7)

def input_numpad_dot():
	press_key(VK_NUMPAD_DECIMAL)

def input_numpad_add():
	press_key(VK_NUMPAD_ADD)

def input_ctrl_numpad_2():
	win32api.keybd_event(VK_CONTROL, 0, 0, 0)
	win32api.keybd_event(VK_NUMPAD2, 0, 0, 0)
	time.sleep(0.1)
	win32api.keybd_event(VK_NUMPAD2, 0, win32con.KEYEVENTF_KEYUP, 0)
	win32api.keybd_event(VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
	time.sleep(0.1)

def main():
	# 启动 "C:\Users\shuidun\Desktop\Shin Megami Tensei V Vengeance v1.0-v1.0.3 Plus 31 Trainer.exe"
	trainer_path = r"C:\Users\shuidun\Desktop\Shin Megami Tensei V Vengeance v1.0-v1.0.3 Plus 31 Trainer.exe"
	os.startfile(trainer_path)
	time.sleep(4)  # 等待训练器启动
	# 1. 按16次tab
	for _ in range(16):
		press_key(VK_TAB)
	# 2. ctrl+a
	press_ctrl_a()
	# 3. 输入0.7（主键盘区）
	input_main_keyboard_07()
	# 4. 按2次tab
	for _ in range(2):
		press_key(VK_TAB)
	# 5. ctrl+a
	press_ctrl_a()
	# 输入0.7（主键盘区）
	input_main_keyboard_07()
	# 按3次tab
	for _ in range(3):
		press_key(VK_TAB)
	# ctrl+a
	press_ctrl_a()
	# 输入0.7（主键盘区）
	input_main_keyboard_07()
	# 输入小键盘区的.
	input_numpad_dot()
	# 输入小键盘区的+
	input_numpad_add()
	# 输入ctrl+小键盘区的2
	input_ctrl_numpad_2()

if __name__ == "__main__":
	main()
