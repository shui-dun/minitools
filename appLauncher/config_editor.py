import wx
import os

class ConfigEditor(wx.Dialog):
    def __init__(self, parent, config_manager):
        super().__init__(parent, title="配置编辑器", size=(800, 500))
        
        self.config_manager = config_manager
        
        # 创建面板和主布局
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 顶部分类选择
        category_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        category_label = wx.StaticText(panel, label="选择分类：")
        category_sizer.Add(category_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        
        self.category_choice = wx.Choice(panel)
        for category in self.config_manager.get_categories():
            self.category_choice.Append(category)
        
        if self.category_choice.GetCount() > 0:
            self.category_choice.SetSelection(0)
        category_sizer.Add(self.category_choice, 1, wx.ALL | wx.EXPAND, 5)
        
        # 添加和删除分类的按钮
        add_category_button = wx.Button(panel, label="添加分类")
        category_sizer.Add(add_category_button, 0, wx.ALL, 5)
        
        rename_category_button = wx.Button(panel, label="重命名")
        category_sizer.Add(rename_category_button, 0, wx.ALL, 5)
        
        remove_category_button = wx.Button(panel, label="删除分类")
        category_sizer.Add(remove_category_button, 0, wx.ALL, 5)
        
        main_sizer.Add(category_sizer, 0, wx.ALL | wx.EXPAND, 5)
        
        # 应用列表
        self.app_listbox = wx.ListBox(panel, style=wx.LB_SINGLE, size=(-1, 200))
        main_sizer.Add(wx.StaticText(panel, label="该分类中的应用:"), 0, wx.ALL, 5)
        main_sizer.Add(self.app_listbox, 1, wx.ALL | wx.EXPAND, 5)
        
        # 路径编辑部分
        path_sizer = wx.BoxSizer(wx.HORIZONTAL)
        path_sizer.Add(wx.StaticText(panel, label="应用路径:"), 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        
        self.path_text = wx.TextCtrl(panel)
        path_sizer.Add(self.path_text, 1, wx.ALL | wx.EXPAND, 5)
        
        main_sizer.Add(path_sizer, 0, wx.ALL | wx.EXPAND, 5)
        
        # 应用操作按钮
        app_button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        add_app_button = wx.Button(panel, label="添加应用")
        app_button_sizer.Add(add_app_button, 1, wx.ALL, 5)
        
        remove_app_button = wx.Button(panel, label="删除应用")
        app_button_sizer.Add(remove_app_button, 1, wx.ALL, 5)
        
        main_sizer.Add(app_button_sizer, 0, wx.ALL | wx.EXPAND, 5)
        
        # 保存和取消按钮
        bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        save_button = wx.Button(panel, label="保存")
        bottom_sizer.Add(save_button, 1, wx.ALL, 5)
        
        cancel_button = wx.Button(panel, label="取消")
        bottom_sizer.Add(cancel_button, 1, wx.ALL, 5)
        
        main_sizer.Add(bottom_sizer, 0, wx.ALL | wx.EXPAND, 10)
        
        panel.SetSizer(main_sizer)
        
        # 绑定事件
        self.category_choice.Bind(wx.EVT_CHOICE, self.on_category_selected)
        add_category_button.Bind(wx.EVT_BUTTON, self.on_add_category)
        remove_category_button.Bind(wx.EVT_BUTTON, self.on_remove_category)
        rename_category_button.Bind(wx.EVT_BUTTON, self.on_rename_category)
        add_app_button.Bind(wx.EVT_BUTTON, self.on_add_app)
        remove_app_button.Bind(wx.EVT_BUTTON, self.on_remove_app)
        save_button.Bind(wx.EVT_BUTTON, self.on_save)
        cancel_button.Bind(wx.EVT_BUTTON, self.on_cancel)
        self.app_listbox.Bind(wx.EVT_LISTBOX, self.on_app_selected)
        
        # 初始化应用列表
        self.update_app_list()
    
    def update_app_list(self):
        self.app_listbox.Clear()
        selection = self.category_choice.GetSelection()
        if selection != wx.NOT_FOUND:
            category = self.category_choice.GetString(selection)
            apps = self.config_manager.get_apps_for_category(category)
            for app in apps:
                self.app_listbox.Append(app)
    
    def on_category_selected(self, event):
        self.update_app_list()
    
    def on_add_category(self, event):
        dialog = wx.TextEntryDialog(self, "输入新分类名称:", "添加分类")
        if dialog.ShowModal() == wx.ID_OK:
            category_name = dialog.GetValue().strip()
            if category_name:
                if self.config_manager.add_category(category_name):
                    self.category_choice.Append(category_name)
                    self.category_choice.SetSelection(self.category_choice.GetCount() - 1)
                    self.update_app_list()
                else:
                    wx.MessageBox("分类已存在", "提示", wx.OK | wx.ICON_INFORMATION)
        dialog.Destroy()
    
    def on_remove_category(self, event):
        selection = self.category_choice.GetSelection()
        if selection != wx.NOT_FOUND:
            category = self.category_choice.GetString(selection)
            if wx.MessageBox(f"确定要删除分类 '{category}' 吗?", "确认", 
                          wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION) == wx.YES:
                if self.config_manager.remove_category(category):
                    self.category_choice.Delete(selection)
                    if self.category_choice.GetCount() > 0:
                        self.category_choice.SetSelection(0)
                    self.update_app_list()
    
    def on_rename_category(self, event):
        selection = self.category_choice.GetSelection()
        if selection != wx.NOT_FOUND:
            old_name = self.category_choice.GetString(selection)
            dialog = wx.TextEntryDialog(self, "输入新分类名称:", "重命名分类", old_name)
            if dialog.ShowModal() == wx.ID_OK:
                new_name = dialog.GetValue().strip()
                if new_name and new_name != old_name:
                    if self.config_manager.update_category_name(old_name, new_name):
                        self.category_choice.Delete(selection)
                        self.category_choice.Insert(new_name, selection)
                        self.category_choice.SetSelection(selection)
                        self.update_app_list()
            dialog.Destroy()
    
    def on_app_selected(self, event):
        selection = self.app_listbox.GetSelection()
        if selection != wx.NOT_FOUND:
            app_path = self.app_listbox.GetString(selection)
            self.path_text.SetValue(app_path)
    
    def on_add_app(self, event):
        selection = self.category_choice.GetSelection()
        if selection != wx.NOT_FOUND:
            category = self.category_choice.GetString(selection)
            app_path = self.path_text.GetValue().strip()
            
            if app_path:
                if self.config_manager.add_app_to_category(category, app_path):
                    self.app_listbox.Append(app_path)
                    self.path_text.Clear()
                else:
                    wx.MessageBox("该应用已存在", "提示", wx.OK | wx.ICON_INFORMATION)
            else:
                wx.MessageBox("请输入有效的应用路径", "提示", wx.OK | wx.ICON_INFORMATION)
    
    def on_remove_app(self, event):
        category_idx = self.category_choice.GetSelection()
        app_idx = self.app_listbox.GetSelection()
        
        if category_idx != wx.NOT_FOUND and app_idx != wx.NOT_FOUND:
            category = self.category_choice.GetString(category_idx)
            app_path = self.app_listbox.GetString(app_idx)
            
            if self.config_manager.remove_app_from_category(category, app_path):
                self.app_listbox.Delete(app_idx)
                self.path_text.Clear()
    
    def on_save(self, event):
        if self.config_manager.save_config():
            wx.MessageBox("配置已保存", "成功", wx.OK | wx.ICON_INFORMATION)
            self.EndModal(wx.ID_OK)
        else:
            wx.MessageBox("保存配置失败", "错误", wx.OK | wx.ICON_ERROR)
    
    def on_cancel(self, event):
        # 重新加载配置以取消更改
        self.config_manager.load_config()
        self.EndModal(wx.ID_CANCEL)
