#NoTrayIcon

#If WinActive("ahk_exe SumatraPDF.exe")

; 复制

+^c::
	Send ^c
	ClipWait  1
	Clipboard := StrReplace(Clipboard, "-`r`n", "")
	Clipboard := StrReplace(Clipboard, "`r`n", " ")
	Clipboard := RegExReplace(Clipboard, "\[\d+\]", "")
Return

#If