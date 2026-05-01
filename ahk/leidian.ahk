; 雷电模拟器相关设置
#IfWinActive, ahk_exe dnplayer.exe

; 向上滚动滚轮：模拟从上 1/4 处匀速滑到下 1/4 处（通常对应内容向下拉）
WheelUp::SwipeLeidian("down")

; 向下滚动滚轮：模拟从下 1/4 处匀速滑到上 1/4 处（通常对应内容向上拉）
WheelDown::SwipeLeidian("up")

SwipeLeidian(direction)
{
    ; 设置坐标模式为相对于当前激活窗口
    CoordMode, Mouse, Window
    
    ; 保存当前鼠标位置
    MouseGetPos, oldX, oldY
    
    ; 获取当前窗口的宽高
    WinGetPos, , , W, H, A
    
    ; 计算关键坐标点
    centerX := W / 2
    
    if (direction = "up") {
        startY := H * 5 / 6
        endY := 0
    } else {
        startY := H / 5
        endY := H
    }

    ; --- 执行动作 ---
    ; 1. 快速移动到起点
    MouseMove, centerX, startY, 0
    ; 2. 按下鼠标
    Click, Down
    ; 3. 匀速滑动到终点 (速度参数 10 可以根据需要调整，0最快，数值越大越慢越匀速)
    MouseMove, centerX, endY, 9
    ; 4. 松开鼠标
    Click, Up
    ; 5. 回到之前鼠标所在的地方
    MouseMove, oldX, oldY, 0
    
    return
}

; 自动滑动
^l::
	if (leidianIsMoving = 0)
    {
        leidianIsMoving := 1
        SetTimer, LeidianMoveDown, 9000
        ; 注意使用TrayTip时，文件编码必须是UTF-8 with BOM
        TrayTip, 自动刷鼠标, 向上移动已启动!
    }
    else
    {
        leidianIsMoving := 0
        SetTimer, LeidianMoveDown, Off
        TrayTip, 自动刷鼠标, 向上移动已停止!
    }
return

LeidianMoveDown:
{
    SwipeLeidian("up")
    return
}

#IfWinActive