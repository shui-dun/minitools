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

; 窗口全屏
F9::
	; 获取屏幕分辨率
	SysGet, ScreenWidth, 78
	SysGet, ScreenHeight, 79
	if (ScreenWidth = 1920 && ScreenHeight = 1080) {
		WinMove, A, , 700, 0, 780, 1850
	} else { ; 2560 × 1440
		WinMove, A, , 680, 0, 1080, 1600
	}
	; 如果存在OnTopReplica.exe，则打开窗口，否则，运行该程序
	if WinExist("ahk_exe OnTopReplica.exe") {
		WinActivate, ahk_exe OnTopReplica.exe
	} else {
		Run, D:\OnTopReplica\OnTopReplica.exe
	}
return

; 窗口最小化
F10::
	WinMinimize, ahk_exe OnTopReplica.exe
	WinMinimize, ahk_exe WeChatAppEx.exe
return

#IfWinActive