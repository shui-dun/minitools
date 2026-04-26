; 雷电模拟器
#IfWinActive, ahk_exe dnplayer.exe

; 拖动效果
WheelDown::MoveMouseLeidian(0, -700)
WheelUp::MoveMouseLeidian(0, 700)

MoveMouseLeidian(x, y)
{
	Click, Down
	MouseMove, x, y, 10, R
	Click, Up
	MouseMove, -x, -y, 0, R
	return
}

#IfWinActive