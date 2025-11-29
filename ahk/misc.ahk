; 右alt映射到右ctrl
RAlt::RControl
; copilot映射到printscreen
<+<#F23::PrintScreen

; 媒体控制快捷键
F2::Send {Media_Play_Pause}
F3::Send {Media_Prev}
F4::Send {Media_Next}
F6::Send {Volume_Mute}
F7::Send {Volume_Down}
F8::Send {Volume_Up}
F9::
    WinMaximize, A
return
F10::
    SendInput {AppsKey} ; 右键菜单
return

; 播放视频时手工模拟下一帧
^!+Right::
	SendInput {Space}
	sleep 25
	SendInput {Space}
Return