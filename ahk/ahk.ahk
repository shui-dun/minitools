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

; 翻译
; ^!s::
;     ; 清空剪贴板并进行复制
;     backUp := Clipboard
;     Clipboard := ""
;     Send ^c
;     ClipWait 2 ; 等待剪贴板的内容到来（剪切板不为空），最多等待2s
;     clipboard := Clipboard
;     ; 删除换行符以及参考文献的引用
;     clipboard := StrReplace(clipboard, "-`r`n", "")
;     clipboard := StrReplace(clipboard, "`r`n", " ")
;     clipboard := RegExReplace(clipboard, "\[[\d, ]+\]([–\-]\[[\d, ]+\])?", "")
;     ; 添加prompt
;     clipboard := "请对以下内容进行中英互翻（如果输入是中文，则翻译为英语，反之，如果输入是英语，则翻译为中文），要求语句流程，符合学术论文规范，如果只给了一个单词，那就输出该单词的多种释义，需要翻译的语句如下：" . clipboard
;     Clipboard := clipboard
;     Loop, 10 {
;         If (WinExist("Claude")) {
;             ; 打开窗口
;             WinActivate
;             MouseMove, 59, 97
;             Sleep, 30
;             Click, Left
;             Sleep, 300
;             ; 点击输入框
;             MouseMove, 493, 422
;             Sleep, 30
;             Click, Left
;             Sleep, 30
;             ; 复制并回车
;             Send, ^v
;             Sleep, 30
;             Send, {Enter}
;             Break
;         } Else {
;             Sleep, 25
;         }
;     }
;     Clipboard := backUp
; Return


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
