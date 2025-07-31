#If WinActive("ahk_exe DR2_us.exe")

; 恢复被覆盖的F2
; 使用SendRaw而不是Send可以发送原始的F2而非被映射的按键（F2::Send {Media_Play_Pause}）
F2::SendRaw {F2}
; enter表示鼠标左键
Enter::Send {LButton}

#If