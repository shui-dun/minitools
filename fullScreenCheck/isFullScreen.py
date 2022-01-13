from ctypes import windll
import win32gui
import win32process
import psutil

user32 = windll.user32
user32.SetProcessDPIAware()  # optional, makes functions return real pixel numbers instead of scaled values

# 屏幕矩形坐标
full_screen_rect = (0, 0, user32.GetSystemMetrics(0), user32.GetSystemMetrics(1))


# 根据window名称获得进程名称
def windowProcessName(window):
    pid = win32process.GetWindowThreadProcessId(window)  # This produces a list of PIDs active window relates to
    return psutil.Process(pid[-1]).name()  # pid[-1] is the most likely to survive last longer


# 判断是否全屏
def isFullScreen():
    try:
        foregroundWindow = win32gui.GetForegroundWindow()  # 获取前台窗口
        rect = win32gui.GetWindowRect(foregroundWindow)  # 获得该窗口的矩形坐标
        processName = windowProcessName(foregroundWindow)  # 获得该窗口的进程名称
        print("window: ({}), rect: ({}), proces: ({})".format(foregroundWindow, rect, processName))
        # 只有前台应用全屏并且不是桌面才返回True
        return rect == full_screen_rect and processName != "explorer.exe"
    except:
        return False
