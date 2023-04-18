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
	; 防止误触ctrl+alt+c
	Sleep, 200
	Send ^c
	ClipWait  5
	Clipboard := StrReplace(Clipboard, "-`r`n", "")
	Clipboard := StrReplace(Clipboard, "`r`n", " ")
	Clipboard := RegExReplace(Clipboard, "\[[\d, ]+\]([–\-]\[[\d, ]+\])?", "")
	Send ^!t
	Loop, 40 {
		If (WinExist("OpenAI Translator")) {
			WinActivate
			; 移动光标（相对于窗口左上角）并点击左键
			MouseMove, 240, 240
			Sleep, 100
			Click, Left
			Send, ^a
			Send, ^v
			; Send, {Enter}
			Break
		} Else {
			Sleep, 50
		}
	}
Return

; ^!s::
	; Send ^c
	; ClipWait  5
	; Clipboard := StrReplace(Clipboard, "-`r`n", "")
	; Clipboard := StrReplace(Clipboard, "`r`n", " ")
	; Clipboard := RegExReplace(Clipboard, "\[[\d, ]+\]([–\-]\[[\d, ]+\])?", "")
	; Send !l
	; Loop, 40 {
		; If (WinExist("沙拉查词") || WinExist("Saladict")) {
			; WinActivate
			; Break
		; } Else {
			; Sleep, 50
		; }
	; }
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

; 手工模拟下一帧

^!+Right::
	Send {Space}
	sleep 25
	Send {Space}
Return