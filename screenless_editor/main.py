import wx
import os
import datetime
import json
import threading
import time
import win32gui

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')

# 读取配置逻辑
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = json.load(f)
    SAVE_DIR = config.get('save_dir', os.getcwd())
else:
    SAVE_DIR = os.getcwd()  # 使用当前脚本运行目录作为保存目录

if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

# 定义生成文件名的函数
def today_filename(idx=1):
    date_str = datetime.datetime.now().strftime('%Y-%m-%d')
    return f"{date_str}_{idx}.md"

# 定义主界面类，继承自wx.Frame
class ScreenlessEditor(wx.Frame):
    def __init__(self):
        # 初始化窗口：无边框(NO_BORDER)、始终置顶(STAY_ON_TOP)
        wx.Frame.__init__(self, None, title='', size=(300, 300), style=wx.NO_BORDER | wx.STAY_ON_TOP)
        self.SetBackgroundColour(wx.Colour(255, 255, 255))  # 设置窗口背景为白色
        # 创建文本框：多行、无边框、禁止纵向滚动条、失去焦点时不隐藏选择内容
        self.text = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.NO_BORDER | wx.TE_NO_VSCROLL | wx.TE_NOHIDESEL)
        self.text.SetBackgroundColour(wx.Colour(0, 0, 0))  # 设置文本框背景为白色（实现隐形）
        self.text.SetForegroundColour(wx.Colour(255, 255, 255))  # 设置文字颜色为白色（打字也看不见）
        # 设置字体
        self.text.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        sizer = wx.BoxSizer(wx.VERTICAL)  # 创建垂直布局管理器
        sizer.Add(self.text, 1, wx.EXPAND)  # 将文本框添加到布局，充满全窗口
        self.SetSizer(sizer)  # 应用布局
        self.Center()  # 将窗口居中显示在屏幕上
        self.file_idx = 1  # 默认文件索引为1
        self.filename = today_filename(self.file_idx)  # 生成默认文件名
        self.filepath = os.path.join(SAVE_DIR, self.filename)
        self.last_content = ''  # 用于记录上次保存的内容，避免重复写入
        self.Bind(wx.EVT_KEY_DOWN, self.on_key_down)  # 绑定窗口按键按下事件
        self.text.Bind(wx.EVT_KEY_DOWN, self.on_key_down)  # 绑定文本框按键按下事件
        self.text.Bind(wx.EVT_TEXT, self.on_text)  # 绑定文字改变事件
        self.save_lock = threading.Lock()  # 创建线程锁，保护文件写入操作
        self.need_save = False  # 是否需要保存的标识位
        # 创建并启动自动保存后台线程
        self.save_timer = threading.Thread(target=self.auto_save, daemon=True)
        self.save_timer.start()
        # 强制位于最上层（保证键盘输入一直被它抓取）
        self.focus_timer = threading.Thread(target=self.keep_focus, daemon=True)
        self.focus_timer.start()
        self.load_file()  # 启动时加载已有文件内容

    # 强制位于最上层
    def keep_focus(self):
        while True:
            time.sleep(0.5)  # 每0.5秒检查一次
            try:
                hwnd = self.GetHandle()  # 获取当前窗口句柄
                # 调用Win32 API强制将窗口带到前台
                win32gui.SetForegroundWindow(hwnd)
            except Exception:
                pass

    # 按键按下事件处理
    def on_key_down(self, event):
        keycode = event.GetKeyCode()  # 获取按下的键码
        control = event.ControlDown()  # 判断Ctrl是否按下
        alt = event.AltDown()  # 判断Alt是否按下
        # 快捷键：Ctrl + Alt + 数字键盘数字 (0-9) 切换文件
        if control and alt and wx.WXK_NUMPAD0 <= keycode <= wx.WXK_NUMPAD9:
            idx = keycode - wx.WXK_NUMPAD0
            self.switch_file(idx)
            return
        # 快捷键：Ctrl + Alt + 普通主键盘数字 (0-9) 切换文件
        elif control and alt and wx.WXK_0 <= keycode <= wx.WXK_9:
            idx = keycode - wx.WXK_0
            self.switch_file(idx)
            return
        event.Skip()  # 允许事件继续传递，确保文字能正常输入

    # 当文字发生变化时
    def on_text(self, event):
        with self.save_lock:
            self.need_save = True  # 标记需要保存
        event.Skip()  # 允许事件传递

    # 自动保存线程函数
    def auto_save(self):
        while True:
            time.sleep(1)  # 每秒检查一次
            with self.save_lock:
                if self.need_save:  # 如果有新改动
                    self.save_file()  # 执行保存
                    self.need_save = False  # 重置标识位

    # 执行写文件操作
    def save_file(self):
        content = self.text.GetValue()  # 获取文本框内全部文字
        if content != self.last_content:  # 只有内容真的变了才写磁盘
            with open(self.filepath, 'w', encoding='utf-8') as f:
                f.write(content)  # 写入文件
            self.last_content = content  # 更新内存缓存

    # 从磁盘读取文件
    def load_file(self):
        if os.path.exists(self.filepath):
            with open(self.filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            self.text.SetValue(content)  # 将内容放入文本框
        else:
            self.text.SetValue('')  # 文件不存在则清空文本框
        wx.CallAfter(self.text.SetInsertionPointEnd)  # 将光标移至末尾，方便继续输入

    # 切换文件逻辑
    def switch_file(self, idx):
        self.save_file()  # 切换前先保存当前文件
        self.file_idx = idx  # 更新索引
        self.filename = today_filename(self.file_idx)
        self.filepath = os.path.join(SAVE_DIR, self.filename)
        self.load_file()

# 定义wx应用程序类
class App(wx.App):
    def OnInit(self):
        self.frame = ScreenlessEditor()  # 实例化主窗口
        self.frame.Show()  # 显示窗口
        return True

# 主入口函数
def main():
    app = App(False)  # 初始化App，False表示不重定向输出到窗口
    app.MainLoop()  # 启动主事件循环

if __name__ == '__main__':
    main()