#NoTrayIcon

#If WinActive("ahk_exe SumatraPDF.exe") || WinActive("ahk_exe CAJVieweru.exe")

; 复制

+^c::
	Send ^c
	ClipWait  1
	Clipboard := StrReplace(Clipboard, "-`r`n", "")
	; 如果含有非ASCII字符（例如中文字符）
	if (RegExmatch(Clipboard, "[^[:ascii:]]")) {
		Clipboard := StrReplace(Clipboard, "`r`n", "")
	} else {
		Clipboard := StrReplace(Clipboard, "`r`n", " ")
	}
	; Clipboard := RegExReplace(Clipboard, "\[[\d, ]+\]([–\-]\[[\d, ]+\])?", "")
Return

#If