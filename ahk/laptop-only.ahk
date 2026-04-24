#Warn ; 启用警告
#SingleInstance Force ; 如果脚本已经在运行，则终止旧实例并启动新实例
; 鼠标中键和Tab切换到标题中含有Gemini的另一个窗口（优先切换到不同于当前窗口的）
MButton::
Tab::
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

