#NoTrayIcon

#If WinActive("ahk_exe Obsidian.exe")

; 包裹公式块

#+z::
	backup := Clipboard
	Clipboard := ""
	Send ^x
	ClipWait  1 
	Clipboard := "`n$$`n" . Clipboard  . "`n$$`n"
	Send ^v
	Clipboard := backup
Return

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
	Clipboard := ""
	Send {Home}+{End}^c
	ClipWait  0.1
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
	Clipboard := backup
}

; 补全公式块

:*:$$`n::$$`n`n$${Up}

; 补全代码块

:*:``````::```````n``````{Up}{End}	

#If



#If WinActive("ahk_exe Obsidian.exe") || WinActive("ahk_exe Typora.exe")

; 段落

#p::
	backup := Clipboard
	Clipboard := ""
	Send +{Home}^c
	ClipWait  1 
	Clipboard := "**" . Clipboard  . ".** "
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

; 包裹inline公式

#z::
	backup := Clipboard
	Clipboard := ""
	Send ^c  ; Send Ctrl+C to get selection on clipboard.
	ClipWait  1  ; Wait for the copied text to arrive at the clipboard.
	Clipboard = %Clipboard% ; strip blank character
	Clipboard := " $" . Clipboard  . "$ " ; quote
	Send ^v ; paste
	Clipboard := backup
Return

; 包裹inline代码
#c::
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