import os
import sys
import json
import subprocess
import datetime
import re
import psutil
import wx
import wx.adv
import yaml
import ctypes

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if not os.path.exists(config_path):
        wx.MessageBox("缺少 config.json 文件，请根据 config.template.json 新建该文件", "配置错误", wx.OK | wx.ICON_ERROR)
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

# 解析 Markdown 文件中的前言 YAML 部分
def parse_log(filepath):
    empty_data = {"historyDates": [], "historyCounts": []}
    if not os.path.exists(filepath):
        # 若日志不存在，初始化空前言
        return empty_data
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    m = re.search(r'^---\s*(.*?)\s*---\s*(.*)$', content, re.DOTALL)
    if not m:
        return empty_data
    frontmatter = m.group(1)
    data = yaml.safe_load(frontmatter)
    # 把historyDates转化为字符串格式
    if "historyDates" in data:
        data["historyDates"] = [date.strftime("%Y-%m-%d") if isinstance(date, datetime.date) else date for date in data["historyDates"]]
    return data if data else empty_data

# 将前言 YAML 部分写回文件
def update_log(filepath, data):
    # 把historyDates转化为日期格式
    if "historyDates" in data:
        data["historyDates"] = [datetime.datetime.strptime(date, "%Y-%m-%d").date() for date in data["historyDates"]]
    frontmatter = "---\n"
    frontmatter += yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)
    frontmatter += "---\n"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(frontmatter)

# 更新今日次数
def increment_today_count(logPath):
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    data = parse_log(logPath)
    if today in data["historyDates"]:
        idx = data["historyDates"].index(today)
        data["historyCounts"][idx] += 1
    else:
        data["historyDates"].append(today)
        data["historyCounts"].append(1)
    update_log(logPath, data)

# 获取今日跳过次数
def get_today_count(logPath):
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    data = parse_log(logPath)
    if today in data["historyDates"]:
        idx = data["historyDates"].index(today)
        return data["historyCounts"][idx]
    return 0

# 杀掉所有 Stretchly.exe 进程
def kill_stretchly():
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] and proc.info['name'].lower() == "stretchly.exe":
            try:
                proc.kill()
            except Exception as e:
                print(f"Error killing process: {e}")

def kill_stretchly_monitor():
    for proc in psutil.process_iter(['name', 'cmdline']):
        if not (proc.info['name'] and proc.info['name'].lower() == "python.exe"):
            continue
        if not (len(proc.info['cmdline']) > 1 and os.path.basename(__file__) in proc.info['cmdline'][1]):
            continue
        if proc.pid == os.getpid():
            continue
        # 如果是当前进程的父/子进程，不杀(pipenv通常会创建一个子进程)
        if proc.ppid() == os.getpid() or proc.pid == os.getppid():
            continue
        try:
            print(f"Killing process {proc.pid}")
            proc.kill()
        except Exception as e:
            print(f"Error killing process: {e}")

# 启动 Stretchly.exe
def launch_stretchly(path):
    try:
        subprocess.Popen([path])
    except Exception as e:
        wx.MessageBox(f"启动Stretchly失败: {e}", "错误", wx.OK | wx.ICON_ERROR)

# 系统托盘图标和菜单
class TaskBarIcon(wx.adv.TaskBarIcon):
    ID_SKIP = wx.NewIdRef()
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.set_icon()
        self.Bind(wx.EVT_MENU, self.on_skip, id=self.ID_SKIP)
    
    def CreatePopupMenu(self):
        menu = wx.Menu()
        menu.Append(self.ID_SKIP, "跳过休息")
        return menu

    def set_icon(self):
        icon = wx.Icon(wx.ArtProvider.GetBitmap(wx.ART_WX_LOGO, wx.ART_OTHER, (32,32)))
        self.SetIcon(icon, "stretchlyMonitor")
    
    def on_skip(self, event):
        logPath = self.config.get("logPath")
        today_count = get_today_count(logPath)
        total_confirm = today_count + 1
        confirmed = 0
        for i in range(total_confirm):
            dlg = wx.MessageDialog(None, f"今日已跳过 {today_count} 次。\n再次确认跳过休息？({i+1}/{total_confirm})", "跳过休息", wx.OK | wx.CANCEL | wx.ICON_NONE)
            if dlg.ShowModal() == wx.ID_OK:
                confirmed += 1
            else:
                dlg.Destroy()
                return
            dlg.Destroy()

        # 当确认达到次数要求时，执行操作
        kill_stretchly()
        launch_stretchly(self.config.get("stretchlyPath"))
        increment_today_count(logPath)

class App(wx.App):
    def OnInit(self):
        # 启用高 DPI 支持，否则字体模糊
        if wx.Platform == "__WXMSW__":
            ctypes.OleDLL('shcore').SetProcessDpiAwareness(1)
        config = load_config()
        self.tbIcon = TaskBarIcon(config)
        return True

if __name__ == "__main__":
    # 先加载图标，显得流畅
    app = App(False)
    kill_stretchly_monitor()
    app.MainLoop()
