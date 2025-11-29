#If WinActive("ahk_exe SumatraPDF.exe") || WinActive("ahk_exe CAJVieweru.exe")

; 复制

+^c::
	Clipboard := ""
	SendInput ^c
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
^Left::SendInput !{Left}
^Right::SendInput !{Right}

#If