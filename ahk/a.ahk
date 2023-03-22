; ; Split string by space and remove newline and replace newline with space

; IsEnglishChar(char) {        ; 判断字符是否为英文字符
	; MsgBox % char
    ; return RegExMatch(char, "[A-Za-z]")
; }

; new_clipboard := RegExReplace(Clipboard, "(.)`r`n(.)", "$1" . (IsEnglishChar("$1") && IsEnglishChar("$2") ? " " : "" . "$2"))

; ; new_clipboard := RegExReplace(Clipboard, "(\w)`r`n(\w)", "$1" . (IsEnglishChar("$1") and IsEnglishChar("$2") ? " " : "" . "$2"))

; MsgBox % new_clipboard


clipboard := Clipboard

; Replace line breaks with spaces if surrounded by English characters
clipboard := RegExReplace(clipboard, "([A-Za-z])[\r\n]+([A-Za-z])", "$1 $2")

; Remove line breaks if not surrounded by English characters
clipboard := RegExReplace(clipboard, "[\r\n]+", "")

Clipboard := clipboard