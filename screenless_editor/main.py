import wx
import os
import datetime
import json
import threading
import time
import win32con
import win32gui

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')

# 读取配置
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = json.load(f)
    SAVE_DIR = config.get('save_dir', os.getcwd())
else:
    SAVE_DIR = os.getcwd()

if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

def today_filename(idx=1):
    date_str = datetime.datetime.now().strftime('%Y-%m-%d')
    return f"{date_str}_{idx}.md"

class ScreenlessEditor(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title='', size=(3, 3), style=wx.NO_BORDER | wx.STAY_ON_TOP)
        self.SetBackgroundColour(wx.Colour(255, 255, 255))
        # 隐藏滚动条，设置TE_NO_VSCROLL，TE_NOHIDESEL
        self.text = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.NO_BORDER | wx.TE_NO_VSCROLL | wx.TE_NOHIDESEL)
        self.text.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.text.SetForegroundColour(wx.Colour(255, 255, 255))
        self.text.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.text, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.Center()
        self.file_idx = 1
        self.filename = today_filename(self.file_idx)
        self.filepath = os.path.join(SAVE_DIR, self.filename)
        self.last_content = ''
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        self.text.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        self.text.Bind(wx.EVT_TEXT, self.on_text)
        self.save_lock = threading.Lock()
        self.need_save = False
        self.save_timer = threading.Thread(target=self.auto_save, daemon=True)
        self.save_timer.start()
        self.focus_timer = threading.Thread(target=self.keep_focus, daemon=True)
        self.focus_timer.start()
        self.load_file()
        self.set_always_on_top()

    def keep_focus(self):
        while True:
            time.sleep(0.5)
            try:
                hwnd = self.GetHandle()
                # 让窗口到前台
                win32gui.SetForegroundWindow(hwnd)
                wx.CallAfter(self.Raise)
                wx.CallAfter(self.text.SetFocus)
            except Exception:
                pass

    def set_always_on_top(self):
        self.Raise()
        self.SetWindowStyleFlag(wx.STAY_ON_TOP | wx.NO_BORDER)
        hwnd = self.GetHandle()
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)


    def on_close(self, event):
        self.save_file()
        self.Destroy()

    def on_key_down(self, event):
        keycode = event.GetKeyCode()
        control = event.ControlDown()
        alt = event.AltDown()
        # Ctrl+Alt+数字切换文件
        if control and alt and wx.WXK_NUMPAD0 <= keycode <= wx.WXK_NUMPAD9:
            idx = keycode - wx.WXK_NUMPAD0
            self.switch_file(idx)
            return
        elif control and alt and wx.WXK_0 <= keycode <= wx.WXK_9:
            idx = keycode - wx.WXK_0
            self.switch_file(idx)
            return
        event.Skip()

    def on_text(self, event):
        with self.save_lock:
            self.need_save = True
        event.Skip()

    def auto_save(self):
        while True:
            time.sleep(1)
            with self.save_lock:
                if self.need_save:
                    self.save_file()
                    self.need_save = False

    def save_file(self):
        content = self.text.GetValue()
        if content != self.last_content:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            self.last_content = content

    def load_file(self):
        if os.path.exists(self.filepath):
            with open(self.filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            self.text.SetValue(content)
        else:
            self.text.SetValue('')
        wx.CallAfter(self.text.SetInsertionPointEnd)

    def switch_file(self, idx):
        self.save_file()
        self.file_idx = idx
        self.filename = today_filename(self.file_idx)
        self.filepath = os.path.join(SAVE_DIR, self.filename)
        self.load_file()

class App(wx.App):
    def OnInit(self):
        self.frame = ScreenlessEditor()
        self.frame.Show()
        return True

def main():
    app = App(False)
    app.MainLoop()

if __name__ == '__main__':
    main()
