#NoTrayIcon

#If WinActive("ahk_exe Obsidian.exe")

; 标题

^0::title(0)
^1::title(1)
^2::title(2)
^3::title(3)
^4::title(4)
^5::title(5)
^6::title(6)

title(times) 
{
	backup := Clipboard
	sleep 100
	Clipboard := ""
	Send {Home}+{End}^c
	; 不知道为啥ClipWait无效，因此改用sleep
	sleep 100
	Clipboard := LTrim(Clipboard, OmitChars := " #")
	if (%times% != 0) 
	{
		Clipboard := " " . Clipboard
		Loop, %times% 
		{
			Clipboard := "#" . Clipboard
		}
	}
	Send ^v
	sleep 100
	Clipboard := backup
}

#If

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

; 部分英文符号覆盖中文符号

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