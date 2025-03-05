#If WinActive("ahk_exe Obsidian.exe") || WinActive("ahk_exe Typora.exe") || WinActive("ahk_exe Notion.exe") || WinActive("ahk_exe Code.exe")

; 段落

!p::
	backup := Clipboard
	Clipboard := ""
	SendInput +{Home}^c
	; 等待剪切板变为非空，最多等待1s
	ClipWait  1 
	if (InStr(Clipboard, "- ") != 0)
	{
		Clipboard := StrReplace(Clipboard, "- ", "- **") . "** "
	} else if (InStr(Clipboard, "* ") != 0)
	{
		Clipboard := StrReplace(Clipboard, "* ", "* **") . "** "
	} else
	{
		Clipboard := "**" . Clipboard  . "** "
	}
	SendInput ^v
	; 等待100ms，再恢复剪切板，防止还没粘贴完，剪切板就被替换为了backup
	sleep 100
	Clipboard := backup
Return

; 取消段落

+!p::
	backup := Clipboard
	Clipboard := ""
	SendInput +{Home}
	sleep 100 ; 使得a显示为**a**，这样才能复制
	SendInput ^c
	ClipWait 1 
	Clipboard := RegExReplace(Clipboard, "\*\*(.+)\*\*\s*", "$1")
	SendInput ^v 
	sleep 100
	Clipboard := backup
	SendInput +{Home} ; 便于下一步进行剪切等操作
Return
	

; 所有标题进一级

^9::
	backup := Clipboard
	Clipboard := ""
	SendInput ^c
	ClipWait  1
	tmpString := ""
	Loop, Parse, Clipboard, `n 
	{
		if (RegExMatch(A_LoopField, "^#+ ") != 0) 
		{
			tmpString := tmpString . "#" . A_LoopField . "`n"
		} else 
		{
			tmpString := tmpString . A_LoopField . "`n"
		}
	}
	Clipboard := tmpString
	SendInput ^v
	sleep 100
	Clipboard := backup
Return

; 所有标题退一级

^8::
	backup := Clipboard
	Clipboard := ""
	SendInput ^c
	ClipWait  1
	tmpString := ""
	Loop, Parse, Clipboard, `n 
	{
		if (RegExMatch(A_LoopField, "^##+ ") != 0) ; 一级标题退无可退
		{
			tmpString := tmpString . StrReplace(A_LoopField, "#", "", 0, 1) . "`n"
		} else 
		{
			tmpString := tmpString . A_LoopField . "`n"
		}
	}
	Clipboard := tmpString
	SendInput ^v
	sleep 100
	Clipboard := backup
Return

; 部分英文符号覆盖中文符号，并自动切换输入法

`::SendInput {U+0060}{Shift}

$::SendInput {U+0024}{Shift}

; 包裹inline数学公式

!m::
	backup := Clipboard
	Clipboard := ""
	SendInput ^c  ; Send Ctrl+C to get selection on clipboard.
	ClipWait  1  ; Wait for the copied text to arrive at the clipboard.
	Clipboard = %Clipboard% ; strip blank character
	Clipboard := " $" . Clipboard  . "$ " ; quote
	SendInput ^v ; paste
	sleep 100
	Clipboard := backup
Return

; 包裹inline代码

!c::
	backup := Clipboard
	Clipboard := ""
	SendInput ^c  ; Send Ctrl+C to get selection on clipboard.
	ClipWait  1  ; Wait for the copied text to arrive at the clipboard.
	Clipboard = %Clipboard% ; strip blank character
	Clipboard := " ``" . Clipboard  . "`` " ; quote
	SendInput ^v ; paste
	sleep 100
	Clipboard := backup
Return

#If