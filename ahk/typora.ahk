#NoTrayIcon

#If WinActive("ahk_exe Typora.exe")

; 方便敲latex公式

::/mat::\begin{{}bmatrix{}}`n\end{{}bmatrix{}}{Up}{End}
::/arr::\begin{{}array{}}{{}ccc{}}`n\end{{}array{}}{Up}{End}
::/ali::\begin{{}aligned{}}`n\end{{}aligned{}}{Up}{End}

::/>::\left<\right>{Left 7}
::/)::\left(\right){Left 7}
::/]::\left[\right]{Left 7}
::/|::\left|\right|{Left 7}
::/\|::\left\|\right\|{Left 8}
::/}::\left\{{}\right\{}}{Left 8}

:*:/bs::\boldsymbol{{}{}}{Left}
:*:/tt::\text{{}{}}{Left}
:*:/bb::\mathbb{{}{}}{Left}
:*:/rm::\mathrm{{}{}}{Left}
:*:/frak::\mathfrak{{}{}}{Left}
:*:/bf::\mathbf{{}{}}{Left}
:*:/cal::\mathcal{{}{}}{Left}

#If