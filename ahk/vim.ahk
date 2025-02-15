; 交换esc和capslock
Esc::Capslock
Capslock::Esc

; 将剪切板内容一个个字符输出（而非粘贴）
; 应用场景：例如，在vim录制宏时，按下<shift+insert>时，vim会记作这个粘贴操作，而不会记住其内容
; 因此，当你的剪切板内容变化后，宏无法正常运行
^!v::
	content := Clipboard
	SendUnicode(content)
Return
; 将字符串转换为Unicode并发送
SendUnicode(str) {
	unicodeString := ""
	Loop, Parse, str
	{
		unicodeString .= "{" . Format("U+{:04X}", Asc(A_LoopField)) . "}"
	}
	SendInput, %unicodeString%
}