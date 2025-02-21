#Warn
#NoTrayIcon
#SingleInstance Force
#Requires AutoHotkey v2.0

class SnippetManager {
    snippetFilePath := "D:\file\cloud\misc\snippet.txt"
    snippets := []
    mainGui := ""
    listView := ""  ; 添加ListView引用
    keyDownHandler := ""
    
    __New() {
        this.InitHotkey()
    }
    
    InitHotkey() {
        HotKey "!^z", (*) => this.ShowMainGui()
    }
    
    ReadSnippets() {
        try {
            fileContent := FileRead(this.snippetFilePath)
            this.snippets.Length := 0  ; 清空数组
            
            for line in StrSplit(fileContent, "`n", "`r") {
                if (line = "")
                    continue
                    
                if (tabPos := InStr(line, "`t")) {
                    alias := Trim(SubStr(line, 1, tabPos - 1))
                    phrase := Trim(SubStr(line, tabPos + 1))
                    phrase := StrReplace(phrase, "\n", "`n")
                    this.snippets.Push({text: phrase, alias: alias})
                } else {
                    MsgBox("snippet解析失败，行内容: " line, "错误", 16)
                    ExitApp()
                }
            }
        } catch Error as e {
            MsgBox("读取snippet文件失败: " e.Message, "错误", 16)
            ExitApp()
        }
    }

    ResolveReferences(text, depth := 0) {
        if (depth > 10) ; 防止循环引用
            return text

        resolved := text
        refPattern := "@\{\{(.+?)\}\}"
        
        while (refStart := RegExMatch(resolved, refPattern, &match)) {
            refAlias := match[1]
            ; 在snippets数组中查找引用的别名
            for snippet in this.snippets {
                if (snippet.alias = refAlias) {
                    referenced := this.ResolveReferences(snippet.text, depth + 1)
                    resolved := RegExReplace(resolved, refPattern, referenced,, 1)
                    break
                }
            }
        }
        
        return resolved
    }
    
    ShowMainGui() {
        if (this.mainGui)
            this.CleanupAndDestroy()
        this.mainGui := Gui("+Resize", "snippet管理器")
        this.mainGui.SetFont("s12")
        this.mainGui.MarginX := 10
        this.mainGui.MarginY := 10
        
        ; 添加搜索框
        this.mainGui.Add("Text",, "搜索snippet:")
        searchBox := this.mainGui.Add("Edit", "w600 Section", "")  ; 使用 Section 标记位置
        searchBox.OnEvent("Change", (ctrl, *) => this.UpdateListView(searchBox.Value))
        
        ; 添加列表视图并保存引用
        this.listView := this.mainGui.Add("ListView", "xs w600 r10 -Multi NoSort", ["序号", "snippet", "完整内容"])
        this.listView.OnEvent("DoubleClick", (ctrl, *) => this.PasteSelectedSnippet())
        
        ; 创建按钮容器
        buttonGroup := this.mainGui.Add("GroupBox", "xs w600 h50", "")  ; 创建一个不可见的组来容纳按钮
        
        ; 添加按钮并使用相对定位
        btnAdd := this.mainGui.Add("Button", "xp+10 yp+15 w80", "添加")
        btnAdd.OnEvent("Click", (*) => this.ShowAddSnippetGui())
        
        btnDelete := this.mainGui.Add("Button", "x+5 w80", "删除")
        btnDelete.OnEvent("Click", (*) => this.DeleteSelectedSnippet())
        
        btnEdit := this.mainGui.Add("Button", "x+5 w80", "编辑")
        btnEdit.OnEvent("Click", (*) => this.EditSelectedSnippet())
        
        btnConfig := this.mainGui.Add("Button", "x+5 w80", "配置文件")
        btnConfig.OnEvent("Click", (*) => Run("explorer.exe /select," this.snippetFilePath))
        
        ; 注册消息处理，没有提供诸如this.mainGui.OnEvent("KeyDown", xxx)的方法也太不健壮了，导致：
        ; 1. 只能监听全局按键，需要判断当前窗口是否是mainGui
        ; 2. 销毁窗口时还需要手动移除消息处理，消息处理的生命周期没有被绑定到窗口上
        this.keyDownHandler := ObjBindMethod(this, "HandleKeyDown")
        OnMessage(0x0100, this.keyDownHandler) ; WM_KEYDOWN
        this.mainGui.OnEvent("Close", (*) => this.CleanupAndDestroy())
        this.mainGui.OnEvent("Escape", (*) => this.CleanupAndDestroy())
        
        ; 初始显示所有snippets
        this.ReadSnippets()
        this.UpdateListView("")
        this.mainGui.Show("w620 h350")
    }

    HandleKeyDown(wParam, lParam, msg, hwnd) {
        ; 检查当前窗口是否是mainGui
        if (!this.mainGui || !WinActive("ahk_id " this.mainGui.Hwnd))
            return

        ; 检查Enter键 (13)
        if (wParam = 13) {
            this.PasteSelectedSnippet()
            return
        }

        ; 检查Ctrl+1到Ctrl+9（使用 "P" 参数判断物理状态）
        if (GetKeyState("Control", "P") && wParam >= 49 && wParam <= 57) {
            index := wParam - 48  ; 转换为数字
            if (this.listView.GetCount() >= index) {
                this.listView.Modify(0, "-Select")  ; 取消所有选择
                this.listView.Modify(index, "Select Focus")
                this.PasteSelectedSnippet()
            }
        }
    }

    CleanupAndDestroy() {
        OnMessage(0x0100, this.keyDownHandler, 0)  ; 必须要移除消息处理
        this.mainGui.Destroy()
    }
    
    UpdateListView(searchTerm) {
        this.listView.Delete()
        index := 1
        
        for snippet in this.snippets {
            displayText := snippet.alias ? snippet.alias : snippet.text
            searchInText := snippet.text " " snippet.alias
            
            if (searchTerm = "" || InStr(searchInText, searchTerm)) {
                indexText := (index <= 9) ? index : ""
                this.listView.Add(, indexText, displayText, snippet.text)
                index++
            }
        }
        
        this.listView.ModifyCol(1, "AutoHdr")
        this.listView.ModifyCol(2, "AutoHdr")
        this.listView.ModifyCol(3, "AutoHdr")
        
        if (this.listView.GetCount() > 0)
            this.listView.Modify(1, "Select Focus")
    }
    
    PasteSelectedSnippet() {
        if (selectedRow := this.listView.GetNext(0)) {
            fullPhrase := this.listView.GetText(selectedRow, 3)
            ; 在粘贴前解析引用
            resolvedPhrase := this.ResolveReferences(fullPhrase)
            
            originalClipboard := A_Clipboard
            Sleep(100)
            A_Clipboard := resolvedPhrase
            this.CleanupAndDestroy()
            Sleep(100)
            Send("^v")
            Sleep(100)
            A_Clipboard := originalClipboard
        }
    }
    
    ShowAddSnippetGui() {
        this.ShowSnippetEditGui("add")
    }
    
    ShowSnippetEditGui(mode, row := 0, alias := "", phrase := "") {
        editGui := Gui("+Resize", (mode="add" ? "添加" : "编辑"))
        editGui.SetFont("s12")
        
        editGui.Add("Text",, "短语:")
        aliasEdit := editGui.Add("Edit", "w600", alias)
        editGui.Add("Text",, "完整内容:")
        phraseEdit := editGui.Add("Edit", "w600 r20", phrase)
        
        btnSave := editGui.Add("Button", "x10", "保存")
        btnSave.OnEvent("Click", (*) => this.SaveSnippet(mode, row, aliasEdit.Value, phraseEdit.Value, editGui))
        
        btnCancel := editGui.Add("Button", "x+5", "取消")
        btnCancel.OnEvent("Click", (*) => editGui.Destroy())
        
        editGui.Show()
    }
    
    SaveSnippet(mode, row, alias, phrase, editGui) {
        phraseForFile := StrReplace(phrase, "`n", "\n")
        if (phraseForFile = "")
            phraseForFile := alias
        if (mode = "add")
            this.InsertNewSnippet(alias, phraseForFile)
        else
            this.EditSnippet(row, alias, phraseForFile)
            
        editGui.Destroy()
        this.ReadSnippets()
        this.UpdateListView("")
    }
    
    DeleteSelectedSnippet() {
        if (selectedRow := this.listView.GetNext(0)) {
            selAlias := this.listView.GetText(selectedRow, 2)
            selPhrase := this.listView.GetText(selectedRow, 3)
            
            result := MsgBox("确定要删除该snippet吗？`n别名: " selAlias, "确认删除", "YesNo")
            if (result != "Yes")
                return
                
            this.RemoveSnippetFromFile(selAlias, selPhrase)
            this.ReadSnippets()
            this.UpdateListView("")
        }
    }
    
    EditSelectedSnippet() {
        if (selectedRow := this.listView.GetNext(0)) {
            selAlias := this.listView.GetText(selectedRow, 2)
            selPhrase := this.listView.GetText(selectedRow, 3)
            this.ShowSnippetEditGui("edit", selectedRow, selAlias, selPhrase)
        }
    }
    
    RemoveSnippetFromFile(targetAlias, targetPhrase) {
        try {
            fileContent := FileRead(this.snippetFilePath)
            newContent := ""
            
            for line in StrSplit(fileContent, "`n", "`r") {
                if (line = "")
                    continue
                    
                if (tabPos := InStr(line, "`t")) {
                    currentAlias := Trim(SubStr(line, 1, tabPos - 1))
                    currentPhrase := StrReplace(Trim(SubStr(line, tabPos + 1)), "\n", "`n")
                    
                    if (currentAlias != targetAlias || currentPhrase != targetPhrase)
                        newContent .= line "`r`n"
                }
            }
            
            FileDelete(this.snippetFilePath)
            FileAppend(RTrim(newContent, "`r`n"), this.snippetFilePath)
        } catch Error as e {
            MsgBox("删除snippet失败: " e.Message, "错误", 16)
        }
    }
    
    EditSnippet(targetRow, alias, phrase) {
        try {
            fileContent := FileRead(this.snippetFilePath)
            newContent := ""
            currentRow := 1
            
            for line in StrSplit(fileContent, "`n", "`r") {
                if (line = "") {
                    currentRow++
                    continue
                }
                
                if (currentRow = targetRow)
                    newContent .= alias "`t" phrase "`r`n"
                else
                    newContent .= line "`r`n"
                    
                currentRow++
            }
            
            FileDelete(this.snippetFilePath)
            FileAppend(RTrim(newContent, "`r`n"), this.snippetFilePath)
        } catch Error as e {
            MsgBox("编辑snippet失败: " e.Message, "错误", 16)
        }
    }
    
    InsertNewSnippet(alias, phrase) {
        try {
            fileContent := FileRead(this.snippetFilePath)
            newContent := alias "`t" phrase "`r`n" fileContent
            
            FileDelete(this.snippetFilePath)
            FileAppend(RTrim(newContent, "`r`n"), this.snippetFilePath)
        } catch Error as e {
            MsgBox("添加snippet失败: " e.Message, "错误", 16)
        }
    }
}

snippetMgr := SnippetManager()