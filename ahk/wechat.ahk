; 微信小程序
#IfWinActive, ahk_exe WeChatAppEx.exe

; 微信小程序中使用拖动效果
Down::MoveMouse(0, -100)
Up::MoveMouse(0, 100)
Right::MoveMouse(-100, 0)
Left::MoveMouse(100, 0)
; Space::Click  ; 空格键模拟鼠标左键点击(视频暂停/播放)，但该功能导致打字出现问题，暂时废弃

MoveMouse(x, y)
{
	Click, Down
	MouseMove, x, y, 0, R  ; 0表示速度设置为最快
	Click, Up
	MouseMove, -x, -y, 0, R
	return
}

#IfWinActive