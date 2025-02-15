﻿#Warn
#SingleInstance Force
#NoTrayIcon

; snippet管理器脚本
global phraseList := []
global snippetFilePath := "D:\file\cloud\misc\snippet.txt"

; 从文件中读取snippet
ReadPhrasesFromFile(snippetFilePath)

; 函数：从文件读取snippet并添加到phraseList
ReadPhrasesFromFile(filePath) {
    FileRead, fileContent, %filePath%
    Loop, Parse, fileContent, `n, `r
    {
        line := A_LoopField
        if (line != "") {
            tabPos := InStr(line, A_Tab) ; 使用Tab作为分隔符
            if (tabPos > 0) {
                alias := Trim(SubStr(line, 1, tabPos - 1))
                phrase := Trim(SubStr(line, tabPos + 1))
            } else { ; 没有别名的情况
                alias := ""
                phrase := Trim(line)
            }
            phrase := StrReplace(phrase, "\n", "`n") ; 替换\n为换行符
            AddPhrase(phrase, alias)
        }
    }
}

AddPhrase(phrase, alias := "") {
    global phraseList
    newPhrase := {}
    newPhrase.text := phrase
    newPhrase.alias := alias
    phraseList.Push(newPhrase)
}

; 显示搜索对话框和列表框
!^z::
    Gui, Destroy ; 销毁已有的GUI
    Gui, +AlwaysOnTop +Resize ; 设置窗口属性：始终在顶部，可调整大小
    Gui, Font, s10
    
    Gui, Add, Text,, 搜索snippet: ; 添加一个文本标签
	; 添加一个宽度为400的编辑框
	; v表示编辑框的内容将被存储在名为SearchTerm的变量中
	; g表示当控件的事件发生时（如编辑框的内容发生变化），将跳转到该标签（UpdateList）执行相应的代码
    Gui, Add, Edit, vSearchTerm w400 gUpdateList
	; 添加一个高度为10行、宽度为400的列表视图
	; 选中的内容将存储在名为 PhraseListView 的变量中
	; 当列表视图中的项目被选择或双击时，程序会跳转到该标签（SelectPhrase）执行相应的代码
	; -Multi禁用多选功能
	; 定义了三列标题：“序号” “snippet” 和 “完整内容”
    Gui, Add, ListView, r10 w400 vPhraseListView gSelectPhrase -Multi, 序号|snippet|完整内容
    Gui, Add, Button, gEditSnippet, 编辑
    
    UpdateListView("")
    
    ; 0x100 表示 Windows 消息 WM_KEYDOWN (按下按键) 的消息标识符
    OnMessage(0x100, "onKeyDown")
    
    ; 显示GUI
    Gui, Show, w420 h300, snippet管理器
    return

; 处理键盘按键
onKeyDown(wParam, lParam) {
    if (wParam = 13) {  ; 13 = VK_RETURN (回车键)
        PasteSelectedPhrase()
    } else if (wParam = 27) {  ; 27 = VK_ESCAPE (Esc键)
        Gui, Destroy
    } else if (wParam >= 49 && wParam <= 57) {  ; Ctrl+1 to Ctrl+9
        if (GetKeyState("Ctrl", "P")) {
            index := wParam - 48
            SelectPhraseByIndex(index)
        }
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
    index := 1
    ; 为每个匹配的snippet添加列表项
    for idx, item in phraseList
    {
        ; 确定显示文本
        displayText := (item.alias != "") ? item.alias : item.text
        ; 创建用于搜索的文本（包含完整snippet和别名）
        searchInText := item.text . " " . item.alias
        ; 如果搜索词为空或者在搜索文本中找到搜索词
        if (searchTerm = "" || InStr(searchInText, searchTerm)) {
            indexText := (index <= 9) ? index : ""
            ; 添加到列表视图
            LV_Add("", indexText, displayText, item.text)
            index++
        }
    }
    ; 自动调整列宽
    LV_ModifyCol(1, "AutoHdr")
    LV_ModifyCol(2, "AutoHdr")
    LV_ModifyCol(3, "AutoHdr")  ; 自动调整第三列（完整内容）的宽度
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

; 粘贴选中的snippet
PasteSelectedPhrase() {
    ; 获取选中的行号
    row := LV_GetNext(0)
    if (row > 0) {  ; 确保有选中的行
        ; 获取第二列的完整snippet
        LV_GetText(fullPhrase, row, 3)
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

; 通过索引选择snippet
SelectPhraseByIndex(index) {
    if (index > 0 && index <= LV_GetCount()) {
        LV_Modify(index, "Select Focus")
        PasteSelectedPhrase()
    }
}

EditSnippet:
    Gui, Destroy ; 关闭窗口
    Run, %snippetFilePath%
return
