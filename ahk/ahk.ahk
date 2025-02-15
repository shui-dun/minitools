#Warn  ; 启用警告
#SingleInstance Force ; 如果脚本已经在运行，则终止旧实例并启动新实例

#Include snippet.ahk
#Include markdown.ahk
#Include pdf.ahk
#Include terminal.ahk
; #Include vim.ahk
#Include wechat.ahk

; ; 方向
; !Left::SendInput {Home}
; !Right::SendInput {End}
; !Up::SendInput {PgUp}
; !Down::SendInput {PgDn}

; +!Left::SendInput +{Home}
; +!Right::SendInput +{End}
; +!Up::SendInput +{PgUp}
; +!Down::SendInput +{PgDn}

; 播放视频时手工模拟下一帧
^!+Right::
	SendInput {Space}
	sleep 25
	SendInput {Space}
Return