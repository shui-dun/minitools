#Warn ; 启用警告
#SingleInstance Force ; 如果脚本已经在运行，则终止旧实例并启动新实例
; 鼠标中键和CapsLock：若当前不在Cherry Studio则先激活它，然后切换标签页
MButton::
CapsLock::
	WinGet, current_id, ID, A
	WinGetTitle, current_title, ahk_id %current_id%
	target_id := ""
	if (InStr(current_title, "Cherry Studio"))
	{
		target_id := current_id
	}
	else
	{
		WinGet, id, List,,, Program Manager
		Loop, %id%
		{
			this_id := id%A_Index%
			WinGetTitle, title, ahk_id %this_id%
			if (InStr(title, "Cherry Studio"))
			{
				target_id := this_id
				break
			}
		}
	}
	if (!target_id)
		return
	if (target_id != current_id)
	{
		WinActivate, ahk_id %target_id%
		Sleep 50
	}
	SendInput ^{Tab}
return

; 右alt映射到右ctrl
RAlt::RControl
; copilot映射到printscreen
<+<#F23::PrintScreen
