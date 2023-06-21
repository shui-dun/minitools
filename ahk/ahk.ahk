; 方向

^Left::Send {Home}
^Right::Send {End}
^Up::Send {PgUp}
^Down::Send {PgDn}

+^Left::Send +{Home}
+^Right::Send +{End}
+^Up::Send +{PgUp}
+^Down::Send +{PgDn}

; 翻译

^!s::
	; 清空剪贴板并进行复制
	Clipboard := ""
	Send ^c
	ClipWait 2 ; 等待剪贴板的内容到来（不为空），最多等待2s
	; 删除换行符以及参考文献的引用
	Clipboard := StrReplace(Clipboard, "-`r`n", "")
	Clipboard := StrReplace(Clipboard, "`r`n", " ")
	Clipboard := RegExReplace(Clipboard, "\[[\d, ]+\]([–\-]\[[\d, ]+\])?", "")
	; 添加引号
	Clipboard := "“" . Clipboard . "”"
	Loop, 10 {
		If (WinExist("LetsTranslate")) {
			; 打开LetsTranslate
			WinActivate
			; 移动光标（相对于窗口左上角）并点击清空当前会话
			MouseMove, 351, 959
			Sleep, 30
			Click, Left
			Sleep, 30
			; 点击输入框
			MouseMove, 515, 947
			Sleep, 30
			Click, Left
			Sleep, 30
			; 复制并回车
			Send, ^v
			Sleep, 30
			Send, {Enter}
			Break
		} Else {
			Sleep, 25
		}
	}
Return

; TIM OCR

^!+o::
	Send +^o ; 这需要先将TIM OCR的默认快捷键修改为shift+ctrl+o
	Loop, 200 {
		If (WinExist("屏幕识图")) {
			WinActivate
			sleep 200
			Send ^c
			ClipWait  1
			WinKill
			Break
		} Else {
			Sleep, 200
		}
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
	; 使用ClipWait前必须要将剪切板置空
	Clipboard := ""
	Send {Home}+{End}^c
	ClipWait, 1
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

#If WinActive("ahk_exe Typora.exe")

; 方便敲latex公式

::/mat::\begin{{}bmatrix{}}`n\end{{}bmatrix{}}{Up}{End}
::/arr::\begin{{}array{}}{{}ccc{}}`n\end{{}array{}}{Up}{End}
::/ali::\begin{{}aligned{}}`n\end{{}aligned{}}{Up}{End}

::/>::\left<\right>{Left 7}
::/)::\left(\right){Left 7}
::/]::\left[\right]{Left 7}
::/|::\left|\right|{Left 7}
::/\|::\left\|\right\|{Left 8}
::/}::\left\{{}\right\{}}{Left 8}

:*:/bs::\boldsymbol{{}{}}{Left}
:*:/tt::\text{{}{}}{Left}
:*:/bb::\mathbb{{}{}}{Left}
:*:/rm::\mathrm{{}{}}{Left}
:*:/frak::\mathfrak{{}{}}{Left}
:*:/bf::\mathbf{{}{}}{Left}
:*:/cal::\mathcal{{}{}}{Left}

#If

#If WinActive("ahk_exe SumatraPDF.exe") || WinActive("ahk_exe CAJVieweru.exe")

; 复制

+^c::
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

#If