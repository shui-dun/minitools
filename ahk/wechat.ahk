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
	; WinMove 参数：窗口标题, 左上角X坐标, 左上角Y坐标, 宽度, 高度
	if (ScreenWidth = 1920 && ScreenHeight = 1080) {
		WinMove, A, , 550, 0, 780, 1850
	} else if (ScreenWidth = 2560 && ScreenHeight = 1440) {
		WinMove, A, , 820, 0, 929, 1850
	} else if (ScreenWidth = 3200 && ScreenHeight = 2000) {
		WinMove, A, , 845, 0, 1483, 2200
	}
return

; 自动滑动
!f::
{
    if (wechatIsMoving = 0)
    {
        wechatIsMoving := 1
        SetTimer, MoveUp, 9000
        TrayTip, 自动刷鼠标, 向上移动已启动!
    }
    else
    {
        wechatIsMoving := 0
        SetTimer, MoveUp, Off
        TrayTip, 自动刷鼠标, 向上移动已停止!
    }
    return
}

MoveUp:
{
    MoveMouse(0, -100)
    return
}

#IfWinActive