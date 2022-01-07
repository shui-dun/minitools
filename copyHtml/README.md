# copyHtml

## 功能

复制网页上的文本，以及latex公式

## 使用步骤

- 复制一段网页上的内容
- 运行该脚本
- 粘贴即可得到处理后的内容

## 支持网站

- 维基百科
- 知乎
- 简书
- 部分支持csdn：csdn的公式可能是katex，也可能是mathjax，但mathjax中的latex公式位于`<script>`标签中，但剪切板并没有保存`<script>`标签的内容，因此无法获取latex公式
- 其他网站：会让你选择是`imgAlt`模式还是`katex`模式