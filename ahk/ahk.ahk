#Warn ; 启用警告
#SingleInstance Force ; 如果脚本已经在运行，则终止旧实例并启动新实例

; 下述脚本暴露了太多了变量、函数、标签
; 而ahk的封装性差得离谱
; 为了不污染全局命名空间
; 所以将这些脚本放在新的进程中运行
Run, snippet.ahk

; 引入其他脚本
#Include misc.ahk
#Include markdown.ahk
#Include pdf.ahk
#Include terminal.ahk
; #Include vim.ahk
#Include wechat.ahk
#Include, danganronpa.ahk
