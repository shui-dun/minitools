; 方向
; 一般来说使用fn + 方向键，但是由于操作系统只接收到 Fn 组合后的“变换后”按键信号，而不会接收到独立的 Fn 键扫描码，因此使用capslock + 方向键来模拟
; 这种 & 是"不严格匹配"，额外的修饰键例如shift不影响触发
CapsLock & Left::HandleDirection("{Home}")
CapsLock & Right::HandleDirection("{End}")
CapsLock & Up::HandleDirection("{PgUp}")
CapsLock & Down::HandleDirection("{PgDn}")

HandleDirection(direction) {
    if GetKeyState("Shift")
        Send % "+" direction
    else 
        Send % direction
    return
}

; 媒体控制快捷键
F2::Send {Media_Play_Pause}
F3::Send {Media_Prev}
F4::Send {Media_Next}
F6::Send {Volume_Mute}
F7::Send {Volume_Down}
F8::Send {Volume_Up}

; 播放视频时手工模拟下一帧
^!+Right::
	SendInput {Space}
	sleep 25
	SendInput {Space}
Return