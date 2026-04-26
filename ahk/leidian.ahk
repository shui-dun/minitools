; 雷电模拟器
#IfWinActive, ahk_exe dnplayer.exe

; 拖动效果
WheelDown::MoveMouseLeidian(0, -800)
WheelUp::MoveMouseLeidian(0, 800)

MoveMouseLeidian(x, y)
{
	Click, Down
	MouseMove, x, y, 4, R
	Click, Up
	MouseMove, -x, -y, 0, R
	return
}

#IfWinActive