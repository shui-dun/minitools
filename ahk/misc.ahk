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