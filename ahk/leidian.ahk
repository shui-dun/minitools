; 雷电模拟器
#IfWinActive, ahk_exe dnplayer.exe

; 拖动效果
WheelDown::MoveMouseLeidian(0, -900)
WheelUp::MoveMouseLeidian(0, 900)

MoveMouseLeidian(x, y)
{
	Click, Down
	MouseMove, x, y, 5, R
	Click, Up
	MouseMove, -x, -y, 0, R
	return
}

#IfWinActive