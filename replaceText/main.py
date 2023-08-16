import re
import os
import traceback
import wx
import json


# 定义TextReplacerApp类，它继承wx.App
class TextReplacerApp(wx.App):

    # 类构造函数
    def __init__(self, *args, **kwargs):
        # 调用父类的构造函数
        super(TextReplacerApp, self).__init__(*args, **kwargs)
        
    # 定义添加忽略文件夹的事件处理函数
    def on_add_folder(self, event):
        # 打开一个对话框，提示用户输入文件夹名称
        folder_name = wx.GetTextFromUser("请输入文件夹名称", "添加文件夹")
        # 如果用户输入了文件夹名称
        if folder_name:
            # 将文件夹名称添加到忽略文件夹列表中
            self.input_ignored_folders.Append(folder_name)

    # 定义移除选择的文件夹的事件处理函数
    def on_remove_folder(self, event):
        # 获取当前选择的文件夹索引
        selection = self.input_ignored_folders.GetSelection()
        # 如果选择了文件夹
        if selection != wx.NOT_FOUND:
            # 从列表中删除该文件夹
            self.input_ignored_folders.Delete(selection)

    # 定义测试替换功能的事件处理函数
    def on_test_replace(self, event):
        try:
            self.writeSettings()
            # 获取测试输入区的文本
            test_input = self.input_test_area_in.GetValue()
            # 将输入区文本中的指定字符串替换为另一个字符串
            test_output = re.sub(self.input_origin.GetValue(), self.input_dest.GetValue(), test_input, int(self.replace_count.GetValue()), flags=re.M)
            # 将替换后的文本显示在测试输出区中
            self.output_test_area_out.SetValue(test_output)
        except Exception as e:
           print(traceback.format_exc())
           wx.MessageBox(traceback.format_exc(), "错误", wx.OK | wx.ICON_ERROR)

    # 定义执行替换功能的事件处理函数
    def on_replace(self, event):
        self.writeSettings()
        self.replaceText()

    def readSettings(self):
        """
        从文件中读取设置
        """
        if not os.path.exists(self.settingPath):
            self.settings = {
                "path": "",
                "origin": "",
                "dest": "",
                "suffix": [],
                "count": 0,
                "ignoredFolders": []
            }
        else:
            with open(self.settingPath, encoding='utf8') as f:
                self.settings = json.load(f)
        self.folder_path.SetPath(self.settings["path"])
        self.input_origin.SetValue(self.settings["origin"])
        self.input_dest.SetValue(self.settings["dest"])
        self.legal_suffix.SetValue(' '.join(self.settings["suffix"]))
        self.replace_count.SetValue(self.settings["count"])
        self.input_ignored_folders.Set(self.settings["ignoredFolders"])
        
    
    def writeSettings(self):
        """
        将设置写入文件
        """
        self.settings["path"] = self.folder_path.GetPath()
        self.settings["origin"] = self.input_origin.GetValue()
        self.settings["dest"] = self.input_dest.GetValue()
        self.settings["suffix"] = self.legal_suffix.GetValue().split()
        # 如果用户没有在后缀前加上.，则自动加上
        for i in range(len(self.settings["suffix"])):
            if self.settings["suffix"][i][0] != '.':
                self.settings["suffix"][i] = '.' + self.settings["suffix"][i]
        self.settings["count"] = self.replace_count.GetValue()
        self.settings["ignoredFolders"] = self.input_ignored_folders.GetStrings()
        with open(self.settingPath, 'w', encoding='utf8') as f:
            json.dump(self.settings, f, ensure_ascii=False, indent=4)


    # 定义应用程序初始化函数
    def OnInit(self):
        # 设置文件应该位于用户的家目录下
        self.settingPath = os.path.join(os.path.expanduser('~'), '.TextReplacer.json')
        # 创建一个新的窗口框架，大小为500x600，标题为"Text Replacer"
        frame = wx.Frame(None, wx.ID_ANY, "Text Replacer", size=(500, 600))
        # 最大化
        frame.Maximize(True)
        # 在窗口框架中创建一个面板
        panel = wx.Panel(frame)
        # 设置字体大小
        font = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL, False, "Consolas")
        panel.SetFont(font)

        # 创建一个垂直布局容器
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        # 创建一个灵活的网格布局容器，每列可以扩展
        flex_sizer = wx.FlexGridSizer(rows=0, cols=2, hgap=5, vgap=10)
        flex_sizer.AddGrowableCol(1, 1)

        # 为某些控件创建引用，以便在事件处理函数中使用
        self.input_origin = wx.TextCtrl(panel)
        self.input_dest = wx.TextCtrl(panel)
        self.legal_suffix = wx.TextCtrl(panel)
        self.folder_path = wx.DirPickerCtrl(panel)
        # 用于替换的次数，应该提供增大和减小的按钮，最小值为0
        self.replace_count = wx.SpinCtrl(panel, value="0", min=0)


        # 创建一个垂直布局容器，用于放置按钮和列表框
        ignored_box = wx.BoxSizer(wx.VERTICAL)
        # 创建"添加"和"删除"按钮
        add_button = wx.Button(panel, label="添加")
        remove_button = wx.Button(panel, label="删除")
        # 创建一个水平布局容器，用于放置按钮
        buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        buttons_sizer.Add(add_button)
        buttons_sizer.Add(remove_button, flag=wx.LEFT, border=5)
        # 创建一个列表框，用于显示忽略的文件夹
        self.input_ignored_folders = wx.ListBox(panel)
        # 将按钮和列表框添加到垂直布局容器中
        ignored_box.Add(buttons_sizer, flag=wx.BOTTOM, border=5)
        ignored_box.Add(self.input_ignored_folders, 1, wx.EXPAND)


        # 测试输入区应该很高
        self.input_test_area_in = wx.TextCtrl(panel, style=wx.TE_MULTILINE, size=(500, 100))
        # 测试输出区应该很高
        self.output_test_area_out = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(500, 100))

        # 定义一个字典，将标签文本映射到控件
        labels_controls = {
            # 标签文本: 创建对应的文本控件
            "被替换的字符串（支持regex）:": self.input_origin,
            "替换成的字符串（可使用 \\1 等语法）:": self.input_dest,
            "合法后缀名（用空格隔开）:": self.legal_suffix,
            "文件夹路径:": self.folder_path,
            "替换次数（0代表替换所有）:": self.replace_count,
            "要忽略的文件夹:": ignored_box,
            "测试输入区:": self.input_test_area_in,
            "测试输出区:": self.output_test_area_out
        }

        # 遍历字典中的每个标签文本和控件
        for label_text, control in labels_controls.items():
            # 为每个标签文本创建一个静态文本控件
            label = wx.StaticText(panel, label=label_text)
            # 将标签和对应的控件添加到灵活的网格布局中
            flex_sizer.Add(label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
            flex_sizer.Add(control, 1, wx.EXPAND | wx.ALL, 5)

        # 将灵活的网格布局添加到主垂直布局中
        main_sizer.Add(flex_sizer, 1, wx.EXPAND | wx.ALL, 10)

        # 创建"测试"和"替换"按钮
        test_button = wx.Button(panel, label="测试测试输入区")
        replace_button = wx.Button(panel, label="替换文件夹中的文件")
        # 创建一个水平布局容器，用于放置按钮
        buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        buttons_sizer.Add(test_button, 1, wx.ALL, 5)
        buttons_sizer.Add(replace_button, 1, wx.ALL, 5)
        # 将水平布局容器添加到主垂直布局中
        main_sizer.Add(buttons_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        # 为每个按钮绑定相应的事件处理函数
        add_button.Bind(wx.EVT_BUTTON, self.on_add_folder)
        remove_button.Bind(wx.EVT_BUTTON, self.on_remove_folder)
        test_button.Bind(wx.EVT_BUTTON, self.on_test_replace)
        replace_button.Bind(wx.EVT_BUTTON, self.on_replace)

        # 将主垂直布局设置为面板的布局
        panel.SetSizer(main_sizer)
        # 调整窗口框架的大小以适应内容
        main_sizer.Fit(frame)
        # 显示窗口框架
        frame.Show()

        # 读取设置
        self.readSettings()
        
        # 返回True表示应用程序初始化成功
        return True
    
    def testSuffix(self, name):
        """
        测试文件名是否符合后缀要求
        """
        for s in self.settings["suffix"]:
            if name[-len(s):] == s:
                return True
        return False


    def replaceText(self):
        """
        替换文本
        """
        # 如果路径为空，或者路径不存在，则直接返回
        if not self.settings["path"] or not os.path.exists(self.settings["path"]):
            wx.MessageBox("路径不存在", "错误", wx.OK | wx.ICON_ERROR)
            return
        for root, subDirs, files in os.walk(self.settings["path"]):
            if os.path.basename(root) in self.settings["ignoredFolders"]:
                # dir = []并没有改变原来的列表，而dir[:] = []则是原地修改列表
                subDirs[:] = []
                continue
            for file in files:
                fullName = os.path.join(root, file)
                if self.testSuffix(fullName):
                    try:
                        with open(fullName, encoding='utf8') as f:
                            s = f.read()
                        sNew = re.sub(self.settings["origin"], self.settings["dest"], s, int(self.settings["count"]), flags=re.M)
                        if sNew != s:
                            print(fullName)
                            # 必须用二进制形式打开，不然会改变换行符
                            with open(fullName, 'wb') as f:
                                f.write(bytes(sNew, encoding="utf8"))
                    except Exception as e:
                        print('in file: {}\t{}'.format(fullName, traceback.format_exc()))
                        wx.MessageBox('in file: {}\t{}'.format(fullName, traceback.format_exc()), "错误", wx.OK | wx.ICON_ERROR)
                        return
        wx.MessageBox("替换完成", "提示", wx.OK | wx.ICON_INFORMATION)


if __name__ == "__main__":
    # 创建TextReplacerApp实例
    app = TextReplacerApp(False)
    # 开始应用程序的主事件循环
    app.MainLoop()

