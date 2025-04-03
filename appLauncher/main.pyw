import wx
import os
import json
import subprocess
import sys
import shlex
from config_manager import ConfigManager
from config_editor import ConfigEditor

class AppLauncherFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="应用启动器", size=(400, 500))
        
        self.config_manager = ConfigManager()
        self.categories = self.config_manager.get_categories()
        
        # 创建面板和垂直布局
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 标题
        title_label = wx.StaticText(panel, label="一键启动器")
        title_label.SetFont(wx.Font(18, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        main_sizer.Add(title_label, 0, wx.ALL | wx.CENTER, 10)
        
        # 创建类别列表
        self.list_box = wx.ListBox(panel, size=(-1, 300))
        self.update_list_box()
        main_sizer.Add(self.list_box, 1, wx.ALL | wx.EXPAND, 10)
        
        # 按钮行
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # 启动按钮
        launch_button = wx.Button(panel, label="启动")
        button_sizer.Add(launch_button, 1, wx.RIGHT, 5)
        
        # 配置按钮
        config_button = wx.Button(panel, label="配置")
        button_sizer.Add(config_button, 1, wx.LEFT, 5)
        
        main_sizer.Add(button_sizer, 0, wx.ALL | wx.EXPAND, 10)
        
        panel.SetSizer(main_sizer)
        
        # 绑定事件
        self.list_box.Bind(wx.EVT_LISTBOX_DCLICK, self.on_launch)
        launch_button.Bind(wx.EVT_BUTTON, self.on_launch)
        config_button.Bind(wx.EVT_BUTTON, self.on_config)
        
        # 绑定键盘事件
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_press)
        
        self.Centre()
        self.Show()
    
    def update_list_box(self):
        """更新列表框，添加序号（1-9）"""
        self.list_box.Clear()
        for i, category in enumerate(self.categories):
            # 只为前9个项目添加序号
            if i < 9:
                self.list_box.Append(f"{i+1}. {category}")
            else:
                self.list_box.Append(f"   {category}")
    
    def on_key_press(self, event):
        """处理键盘按键事件"""
        key_code = event.GetKeyCode()
        is_ctrl = event.ControlDown()
        
        # 检查是否按下 Ctrl + 数字键 (1-9)
        if is_ctrl and ord('1') <= key_code <= ord('9'):
            index = key_code - ord('1')  # 将按键转为索引(0-8)
            if index < len(self.categories):
                # 选择并启动对应项目
                self.list_box.SetSelection(index)
                self.launch_selected_category()
                return
                
        event.Skip()
    
    def launch_selected_category(self):
        """启动选中的类别"""
        selection = self.list_box.GetSelection()
        if selection != wx.NOT_FOUND:
            category = self.categories[selection]  # 直接从列表获取类别名称
            apps = self.config_manager.get_apps_for_category(category)
            
            launch_success = True
            for app_command in apps:
                try:
                    if sys.platform == 'win32':
                        # Windows平台处理
                        subprocess.Popen(app_command, shell=True)
                    else:
                        # Linux/Mac平台处理
                        args = shlex.split(app_command)
                        subprocess.Popen(args)
                except Exception as e:
                    launch_success = False
                    wx.MessageBox(f"无法启动应用 {app_command}: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
            
            # 如果所有应用都成功启动，则关闭窗口
            if launch_success:
                self.Close()
    
    def on_launch(self, event):
        self.launch_selected_category()
    
    def on_config(self, event):
        config_editor = ConfigEditor(self, self.config_manager)
        config_editor.ShowModal()
        # 更新列表
        self.categories = self.config_manager.get_categories()
        self.update_list_box()
        
if __name__ == "__main__":
    app = wx.App()
    frame = AppLauncherFrame()
    app.MainLoop()
