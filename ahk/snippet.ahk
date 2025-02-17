#Warn
#SingleInstance Force
#NoTrayIcon

; snippet管理器脚本
global phraseList := []
global snippetFilePath := "D:\file\cloud\misc\snippet.txt"

; 从文件中读取snippet
ReadPhrasesFromFile(snippetFilePath)

; 函数：从文件读取snippet并添加到phraseList
ReadPhrasesFromFile(filePath) {
    phraseList := [] ; 清空phraseList
    FileRead, fileContent, %filePath%
    Loop, Parse, fileContent, `n, `r
    {
        line := A_LoopField
        if (line != "") {
            tabPos := InStr(line, A_Tab) ; 使用Tab作为分隔符
            if (tabPos > 0) {
                localAlias := Trim(SubStr(line, 1, tabPos - 1))
                localPhrase := Trim(SubStr(line, tabPos + 1))
            } else { ; 没有别名的情况
                ; 报错，解析失败
                MsgBox, 16, 错误, snippet管理器无法解析文件内容`n行内容: %line%
                ; 退出
                ExitApp
            }
            localPhrase := StrReplace(localPhrase, "\n", "`n") ; 替换\n为换行符
            AddPhrase(localPhrase, localAlias)
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
    Gui, 1:Destroy ; 销毁已有的GUI
    Gui, 1:+AlwaysOnTop +Resize ; 设置窗口属性：始终在顶部，可调整大小
    Gui, 1:Font, s10
    
    Gui, 1:Add, Text,, 搜索snippet: ; 添加一个文本标签
	; 添加一个宽度为400的编辑框
	; v表示编辑框的内容将被存储在名为SearchTerm的变量中
	; g表示当控件的事件发生时（如编辑框的内容发生变化），将跳转到该标签（UpdateList）执行相应的代码
    Gui, 1:Add, Edit, vSearchTerm w400 gUpdateList
	; 添加一个高度为10行、宽度为400的列表视图
	; 选中的内容将存储在名为 PhraseListView 的变量中
	; 当列表视图中的项目被选择或双击时，程序会跳转到该标签（SelectPhrase）执行相应的代码
	; -Multi禁用多选功能
	; 定义了三列标题：“序号” “snippet” 和 “完整内容”
    Gui, 1:Add, ListView, r10 w400 vPhraseListView gSelectPhrase -Multi, 序号|snippet|完整内容
    ; 使用固定坐标定位按钮，确保它们在同一行，之后再找有没有更优雅的排版方法
    Gui, 1:Add, Button, x10 y240 w80 gAddSnippet, 添加
    Gui, 1:Add, Button, x95 y240 w80 gDeleteSnippet, 删除
    Gui, 1:Add, Button, x180 y240 w80 gEditSelectedSnippet, 编辑
    Gui, 1:Add, Button, x265 y240 w80 gEditSnippet, 配置文件
    
    UpdateListView("")
    
    ; 0x100 表示 Windows 消息 WM_KEYDOWN (按下按键) 的消息标识符
    OnMessage(0x100, "onKeyDown")
    
    ; 显示GUI
    Gui, 1:Show, w420 h300, snippet管理器
    return

; 处理键盘按键
onKeyDown(wParam, lParam) {
    if (wParam = 13) {  ; 13 = VK_RETURN (回车键)
        PasteSelectedPhrase()
    } else if (wParam = 27) {  ; 27 = VK_ESCAPE (Esc键)
        Gui, Destroy
    } else if (wParam >= 49 && wParam <= 57) {  ; Ctrl+1 to Ctrl+9
        if (GetKeyState("Ctrl", "P")) {
            rowNum := wParam - 48
            SelectPhraseByIndex(rowNum)
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
    Gui, 1:Default  ; 确保操作的是主窗口的ListView
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
    local selectedRow := LV_GetNext(0)
    if (selectedRow > 0) {  ; 确保有选中的行
        ; 获取第二列的完整snippet
        LV_GetText(fullPhrase, selectedRow, 3)
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

AddSnippet:
    CreateSnippetGUI("add")
return

DeleteSnippet:
    row := LV_GetNext(0)
    if (row > 0) {
        ; 获取选中的别名和完整内容
        LV_GetText(selAlias, row, 2)
        LV_GetText(selPhrase, row, 3)
        ; 从文件中删除选中行
        RemoveLineFromFile(snippetFilePath, selAlias, selPhrase)
        ; 重新读取文件内容并更新列表
        ReadPhrasesFromFile(snippetFilePath)
        UpdateListView("")
    }
    return

EditSelectedSnippet:
    row := LV_GetNext(0)
    if (row > 0) {
        ; 获取选中的别名和完整内容
        LV_GetText(selAlias, row, 2)
        LV_GetText(selPhrase, row, 3)
        CreateSnippetGUI("edit", row, selAlias, selPhrase)
    }
return

CreateSnippetGUI(mode, row := 0, alias := "", phrase := "") {
    ; 使用GUI 2来创建编辑窗口，与主窗口(GUI 1)分开
    Gui, 2:New, +AlwaysOnTop
    Gui, 2:Add, Text,, 短语:
    Gui, 2:Add, Edit, vAliasInput w400, %alias%
    Gui, 2:Add, Text,, 完整内容:
    Gui, 2:Add, Edit, vPhraseInput w400 r10, %phrase%
    Gui, 2:Add, Button, x10 g2SaveSnippet, 保存
    Gui, 2:Add, Button, x+5 g2CancelSnippet, 取消
    Gui, 2:Show,, % (mode="add" ? "添加" : "编辑")
    Gui, 2:+OwnDialogs
    GuiControl, 2:, AliasInput, %alias%
    GuiControl, 2:, PhraseInput, %phrase%
    Global snippetMode := mode, snippetRow := row
}

2SaveSnippet:
    Gui, 2:Submit
    alias := AliasInput
    phraseForFile := StrReplace(PhraseInput, "`n", "\n")
    if (snippetMode = "add") {
        InsertNewSnippetAtTop(snippetFilePath, alias, phraseForFile)
    } else {
        EditLineInFile(snippetFilePath, snippetRow, alias, phraseForFile)
    }
    Gui, 2:Destroy
    ; 重新读取文件内容
    ReadPhrasesFromFile(snippetFilePath)
    ; 清空主窗口的列表视图并更新
    Gui, 1:Default  ; 设置默认GUI为主窗口
    UpdateListView("")
    return

2CancelSnippet:
    Gui, 2:Destroy
return

RemoveLineFromFile(filePath, targetAlias, targetPhrase) {
    FileRead, fileContent, %filePath%
    lines := StrSplit(fileContent, "`n", "`r")
    newContent := ""
    Loop, % lines.MaxIndex() {
        currentLine := Trim(lines[A_Index])
        if (currentLine = "")
            continue
            
        tabPos := InStr(currentLine, A_Tab)
        if (tabPos > 0) {
            currentAlias := Trim(SubStr(currentLine, 1, tabPos - 1))
            currentPhrase := StrReplace(Trim(SubStr(currentLine, tabPos + 1)), "\n", "`n")
        } else {
            currentAlias := ""
            currentPhrase := StrReplace(Trim(currentLine), "\n", "`n")
        }
        
        if (currentAlias != targetAlias || currentPhrase != targetPhrase)
            newContent .= currentLine . "`r`n"
    }
    FileDelete, %filePath%
    FileAppend, % RTrim(newContent, "`r`n"), %filePath%
}

EditLineInFile(filePath, targetRow, alias, phrase) {
    FileRead, fileContent, %filePath%
    lines := StrSplit(fileContent, "`n", "`r")
    newContent := ""
    Loop, % lines.MaxIndex() {
        currentLine := Trim(lines[A_Index])
        if (currentLine = "")
            continue
            
        if (A_Index = targetRow)
            newContent .= (alias ? alias : "") . A_Tab . phrase . "`r`n"
        else
            newContent .= currentLine . "`r`n"
    }
    FileDelete, %filePath%
    FileAppend, % RTrim(newContent, "`r`n"), %filePath%
}

InsertNewSnippetAtTop(filePath, alias, phrase) {
    FileRead, fileContent, %filePath%
    ; 如果phrase为空，则设为alias
    if (phrase = "") {
        phrase := alias
    }
    newContent := (alias ? alias : "") . A_Tab . phrase . "`r`n" . fileContent
    FileDelete, %filePath%
    FileAppend, % RTrim(newContent, "`r`n"), %filePath%
}
