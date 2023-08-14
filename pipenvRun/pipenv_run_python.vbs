Set objShell = CreateObject("WScript.Shell")

' 获取当前文件的目录
fileDir = Left(WScript.Arguments(0), InStrRev(WScript.Arguments(0), "\") - 1)
' 调用 pipenv
command = "cmd /c cd /d " & fileDir & " && pipenv run python """ & WScript.Arguments(0) & """"

' 0 表示隐藏窗口
objShell.Run command, 0, False
