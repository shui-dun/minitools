; 方向

; !Left::Send {Home}
; !Right::Send {End}
; !Up::Send {PgUp}
; !Down::Send {PgDn}

; +!Left::Send +{Home}
; +!Right::Send +{End}
; +!Up::Send +{PgUp}
; +!Down::Send +{PgDn}

; 交换esc和capslock
Esc::Capslock
Capslock::Esc

; 复制与粘贴控制台的文本
; 由于键盘没有insert键，所以将ctrl+pause键映射为ctrl+insert键，将shift+pause键映射为shift+insert键
; 注意ctrl+pause会被转化为ctrlbreak，所以最后是将ctrlbreak映射为ctrl+insert
^CtrlBreak::^Insert
+Pause::+Insert
!Pause::!Insert

; 将剪切板内容一个个字符输出（而非粘贴）
; 应用场景：例如，在vim录制宏时，按下<shift+insert>时，vim会记作这个粘贴操作，而不会记住其内容
; 因此，当你的剪切板内容变化后，宏无法正常运行
^!v::
	content := Clipboard
	Loop, Parse, content
	{
		; SendRaw 相比于 Send，不会转义{}等特殊字符
		SendRaw %A_LoopField%
		Sleep 10
	}
Return

; 播放视频时手工模拟下一帧

^!+Right::
	Send {Space}
	sleep 25
	Send {Space}
Return

#If WinActive("ahk_exe Obsidian.exe") || WinActive("ahk_exe Typora.exe")

; 段落

!p::
	backup := Clipboard
	Clipboard := ""
	Send +{Home}^c
	ClipWait  1 
	if (InStr(Clipboard, "- ") != 0)
	{
		Clipboard := StrReplace(Clipboard, "- ", "- **") . ".** "
	} else if (InStr(Clipboard, "* ") != 0)
	{
		Clipboard := StrReplace(Clipboard, "* ", "* **") . ".** "
	} else
	{
		Clipboard := "**" . Clipboard  . ".** "
	}
	Send ^v 
	Clipboard := backup
Return

; 取消段落

+!p::
	backup := Clipboard
	Clipboard := ""
	Send ^c
	ClipWait 1 
	Clipboard := RegExReplace(Clipboard, "\*\*(.+)\.\*\* ", "$1")
	Send ^v 
	Clipboard := backup
Return
	

; 所有标题进一级

^9::
	Clipboard := ""
	Send ^c
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
	Send ^v
Return

; 所有标题退一级

^8::
	Clipboard := ""
	Send ^c
	ClipWait  1
	tmpString := ""
	Loop, Parse, Clipboard, `n 
	{
		if (RegExMatch(A_LoopField, "^#+ ") != 0) 
		{
			tmpString := tmpString . StrReplace(A_LoopField, "#", "", 0, 1) . "`n"
		} else 
		{
			tmpString := tmpString . A_LoopField . "`n"
		}
	}
	Clipboard := tmpString
	Send ^v
Return

; 部分英文符号覆盖中文符号，并自动切换输入法

`::Send {U+0060}{Shift}

$::Send {U+0024}{Shift}

; 包裹inline数学公式

!m::
	Clipboard := ""
	Send ^c  ; Send Ctrl+C to get selection on clipboard.
	ClipWait  1  ; Wait for the copied text to arrive at the clipboard.
	Clipboard = %Clipboard% ; strip blank character
	Clipboard := " $" . Clipboard  . "$ " ; quote
	Send ^v ; paste
Return

; 包裹inline代码

!c::
	backup := Clipboard
	Clipboard := ""
	Send ^c  ; Send Ctrl+C to get selection on clipboard.
	ClipWait  1  ; Wait for the copied text to arrive at the clipboard.
	Clipboard = %Clipboard% ; strip blank character
	Clipboard := " ``" . Clipboard  . "`` " ; quote
	Send ^v ; paste
	Clipboard := backup
Return

#If

#If WinActive("ahk_exe SumatraPDF.exe") || WinActive("ahk_exe CAJVieweru.exe")

; 复制

+^c::
	Clipboard := ""
	Send ^c
	ClipWait  1
	clipboard := Clipboard
	; 恢复中途换行的单词
	clipboard := StrReplace(clipboard, "-`r`n", "")
	; 将英语单词之间的换行符变为空格
	clipboard := RegExReplace(clipboard, "([A-Za-z])[\r\n]+([A-Za-z])", "$1 $2")
	; 删去剩下的换行符（即中文字符间的换行符）
	clipboard := RegExReplace(clipboard, "[\r\n]+", "")
	; 删除参考文献的引用
	; clipboard := RegExReplace(clipboard, "\[[\d, ]+\]([–\-]\[[\d, ]+\])?", "")
	Clipboard := clipboard
Return

; 将ctrl+left和ctrl+right映射为alt+left和alt+right进行跳转，因为sumatra的alt+left和alt+right快捷键已经被占用了
^Left::Send !{Left}
^Right::Send !{Right}

#If
