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

#x::
	Send ^c
	ClipWait  1
	Clipboard := StrReplace(Clipboard, "-`r`n", "")
	Clipboard := StrReplace(Clipboard, "`r`n", " ")
	Clipboard := RegExReplace(Clipboard, "\[[\d, ]+\]", "")
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

^!i::
	Send ^!o
	Loop, 200 {
		If (WinExist("屏幕识图")) {
			WinActivate
			sleep 100
			Send ^c
			ClipWait  1
			WinKill
			Break
		} Else {
			Sleep, 100
		}
	}
Return

^!+i::
	backupclip := Clipboard
	Send ^!o
	Loop, 200 {
		If (WinExist("屏幕识图")) {
			WinActivate
			Send ^c
			ClipWait  1
			WinKill
			Clipboard := backupclip . Clipboard 
			Break
		} Else {
			Sleep, 100
		}
	}
Return

; 手工模拟下一帧

^!+Right::
	Send {Space}
	sleep 25
	Send {Space}
Return
