#Warn
#SingleInstance Force
#NoTrayIcon

; 短语选择器脚本
global phraseList := []

; 添加短语，可选别名（如果不需要别名，第二个参数留空）
AddPhrase("您好，很高兴为您服务。", "问候")
AddPhrase("感谢您的来信，我们会尽快回复。", "感谢信")
AddPhrase("如有任何疑问，请随时联系我。")
AddPhrase("请确认您已收到此信息。", "确认接收")
AddPhrase("祝您有美好的一天！")
AddPhrase("根据我们公司的政策，所有申请将在5个工作日内处理完毕。如有特殊情况，我们会及时通知您。", "处理政策")
AddPhrase("我们已收到您的反馈，技术团队正在解决此问题。我们将在24小时内回复您。", "技术支持")
AddPhrase("此为自动回复邮件，请勿直接回复。") ; 原代码这里有个拼写错误 AddPhrase

AddPhrase(phrase, alias := "") {
    global phraseList
    newPhrase := {}
    newPhrase.text := phrase
    newPhrase.alias := alias
    phraseList.Push(newPhrase)
}

; 显示搜索对话框和列表框
!+^s::
    Gui, Destroy ; 销毁已有的GUI
    Gui, +AlwaysOnTop +Resize ; 设置窗口属性：始终在顶部，可调整大小
    Gui, Font, s10
    
    Gui, Add, Text,, 搜索短语: ; 添加一个文本标签
	; 添加一个宽度为400的编辑框
	; v表示编辑框的内容将被存储在名为SearchTerm的变量中
	; g表示当控件的事件发生时（如编辑框的内容发生变化），将跳转到该标签（UpdateList）执行相应的代码
    Gui, Add, Edit, vSearchTerm w400 gUpdateList
	; 添加一个高度为10行、宽度为400的列表视图
	; 选中的内容将存储在名为 PhraseListView 的变量中
	; 当列表视图中的项目被选择或双击时，程序会跳转到该标签（SelectPhrase）执行相应的代码
	; -Multi禁用多选功能
	; 定义了两列标题：“短语” 和 “完整内容”
    Gui, Add, ListView, r10 w400 vPhraseListView gSelectPhrase -Multi, 短语|完整内容
    
    UpdateListView("")
    
    ; 0x100 表示 Windows 消息 WM_KEYDOWN (按下按键) 的消息标识符
    OnMessage(0x100, "onKeyDown")
    
    ; 显示GUI
    Gui, Show, w420 h300, 短语选择器
    return

; 处理键盘按键
onKeyDown(wParam, lParam) {
    if (wParam = 13) {  ; 13 = VK_RETURN (回车键)
        PasteSelectedPhrase()
    }
}

; 当搜索框内容变化时更新列表
; 这种语法叫做标签
UpdateList:
    Gui, Submit, NoHide ; ahk竟然需要手动提交变量，也就是将GUI里面的内容传递给指定变量
    UpdateListView(SearchTerm)
    return

; 更新列表视图
UpdateListView(SearchTerm) {
    global phraseList
    ; 清空列表
    LV_Delete()
    ; 为每个匹配的短语添加列表项
    for index, item in phraseList
    {
        ; 确定显示文本
        displayText := (item.alias != "") ? item.alias : item.text
        ; 创建用于搜索的文本（包含完整短语和别名）
        searchInText := item.text . " " . item.alias
        ; 如果搜索词为空或者在搜索文本中找到搜索词
        if (searchTerm = "" || InStr(searchInText, searchTerm)) {
            ; 添加到列表视图
            LV_Add("", displayText, item.text)
        }
    }
    ; 自动调整列宽
    LV_ModifyCol(1, "AutoHdr")
    LV_ModifyCol(2, 0)  ; 隐藏第二列（完整内容）
    ; 如果有项目，选中第一项
    if (LV_GetCount() > 0)
        LV_Modify(1, "Select Focus")
}

; 处理列表项选择
SelectPhrase:
    if (A_GuiEvent = "DoubleClick") {
        PasteSelectedPhrase()
    }
    return

; 粘贴选中的短语
PasteSelectedPhrase() {
    ; 获取选中的行号
    row := LV_GetNext(0)
    if (row > 0) {  ; 确保有选中的行
        ; 获取第二列的完整短语
        LV_GetText(fullPhrase, row, 2)
        ; 复制到剪贴板
        Clipboard := fullPhrase
        ; 关闭GUI
        Gui, Destroy
        ; 等待一下确保GUI完全关闭
        Sleep, 100
        ; 粘贴文本
        Send ^v
    }
}
