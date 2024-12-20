; 将字符串转换为Unicode并发送
SendUnicode(str) {
    unicodeString := ""
    Loop, Parse, str
    {
        unicodeString .= "{" . Format("U+{:04X}", Asc(A_LoopField)) . "}"
    }
    SendInput, %unicodeString%
}

; 方向

; !Left::SendInput {Home}
; !Right::SendInput {End}
; !Up::SendInput {PgUp}
; !Down::SendInput {PgDn}

; +!Left::SendInput +{Home}
; +!Right::SendInput +{End}
; +!Up::SendInput +{PgUp}
; +!Down::SendInput +{PgDn}

; 交换esc和capslock
; Esc::Capslock
; Capslock::Esc

; 将剪切板内容一个个字符输出（而非粘贴）
; 应用场景：例如，在vim录制宏时，按下<shift+insert>时，vim会记作这个粘贴操作，而不会记住其内容
; 因此，当你的剪切板内容变化后，宏无法正常运行
^!v::
	content := Clipboard
	SendUnicode(content)
Return

; 播放视频时手工模拟下一帧

^!+Right::
	SendInput {Space}
	sleep 25
	SendInput {Space}
Return

#If WinActive("ahk_exe Obsidian.exe") || WinActive("ahk_exe Typora.exe") || WinActive("ahk_exe Notion.exe")

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
		if (RegExMatch(A_LoopField, "^#+ ") != 0) 
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

#If WinActive("ahk_exe Xshell.exe")

; 粘贴
^v::SendInput +{Insert}

#If