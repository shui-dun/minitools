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

; 鼠标中键切换到标题中含有Gemini的另一个窗口（优先切换到不同于当前窗口的）
MButton::
	WinGet, id, List,,, Program Manager
	WinGet, current_id, ID, A
	found := 0
	first_gemini_id := ""
	Loop, %id%
	{
		this_id := id%A_Index%
		WinGetTitle, title, ahk_id %this_id%
		if (InStr(title, "Gemini"))
		{
			if (!first_gemini_id)
				first_gemini_id := this_id
			if (this_id != current_id) {
				WinActivate, ahk_id %this_id%
				found := 1
				break
			}
		}
	}
	if (!found && first_gemini_id) {
		WinActivate, ahk_id %first_gemini_id%
	}
return

