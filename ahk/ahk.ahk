#Warn ; 启用警告
#SingleInstance Force ; 如果脚本已经在运行，则终止旧实例并启动新实例

; ahkv1中，全局变量必须放在所有函数前面
#Include wechat.global.ahk

; 引入 ahkv2 的脚本：
Run, snippet.ahk

; 引入 ahkv1 脚本
#Include misc.ahk
#Include markdown.ahk
#Include pdf.ahk
#Include wechat.ahk
