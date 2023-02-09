; 方向

^Left::Send {Home}
^Right::Send {End}
^Up::Send {PgUp}
^Down::Send {PgDn}

+^Left::Send +{Home}
+^Right::Send +{End}
+^Up::Send +{PgUp}
+^Down::Send +{PgDn}

; 沙拉查词

^!s::
	Send ^c
	ClipWait  1
	Clipboard := StrReplace(Clipboard, "-`r`n", "")
	Clipboard := StrReplace(Clipboard, "`r`n", " ")
	Clipboard := RegExReplace(Clipboard, "\[[\d, ]+\]([–\-]\[[\d, ]+\])?", "")
	Send !l
	Loop, 40 {
		If (WinExist("沙拉查词") || WinExist("Saladict")) {
			WinActivate
			Break
		} Else {
			Sleep, 50
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

; 手工模拟下一帧

^!+Right::
	Send {Space}
	sleep 25
	Send {Space}
Return