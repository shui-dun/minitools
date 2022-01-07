import re
import pyperclip
from bs4 import BeautifulSoup
import copy

# 存储处理后的结果
ans = ""

# 处理latex公式
def handleLatex(origin):
    if origin is None or origin == "":
        return ""
    # 去除两边的空白
    origin = origin.strip()
    # 将多个空白替换为一个空格
    origin = re.sub(r'\s+', ' ', origin)
    # 多行公式进行换行
    origin = re.sub(r'\\\\ *', r'\\\\\r\n', origin)
    # 长公式使用$$围住
    if '\\\\' in origin or len(origin) > 32:
        return '\r\n\r\n$$\r\n{}\r\n$$\r\n\r\n'.format(origin)
    # 短公式用$围住
    else:
        return ' ${}$ '.format(origin)


def wikipedia(soup):
    global ans
    # 最底层的元素，直接追加到结果中
    if not hasattr(soup, "children"):
        ans += soup
        return
    # latex公式位于img的alt属性中
    if soup.name == "img":
        try:
            ans += handleLatex(soup['alt'])
        except:
            pass
        return
    # 跳过annotation标签
    if soup.name == "annotation":
        return
    # 遍历子标签
    for child in soup.children:
        wikipedia(child)


def zhihu(soup):
    global ans
    if not hasattr(soup, "children"):
        ans += soup
        return
    if soup.name == "img":
        try:
            # zhihu的latex代码存放在img的data-formula属性中
            ans += handleLatex(soup['data-formula'])
        except Exception as e:
            print(e)
        return
    for child in soup.children:
        zhihu(child)


def katex(soup):
    global ans
    if not hasattr(soup, "children"):
        ans += soup
        return
    # katex的latex公式存放在<span class="katex-mathml">标签的text中
    if soup.has_attr('class') and "katex-mathml" in soup['class']:
        try:
            ans += handleLatex(soup.text)
        except Exception as e:
            print(e)
        return
    if soup.has_attr('class') and "katex-html" in soup['class']:
        return
    for child in soup.children:
        katex(child)


def imgAlt(soup):
    global ans
    if not hasattr(soup, "children"):
        ans += soup
        return
    if soup.name == "img":
        try:
            # latex代码存放在img的alt属性中
            ans += handleLatex(soup['alt'])
        except Exception as e:
            print(e)
        return
    for child in soup.children:
        imgAlt(child)

# 通过网址选择使用哪种方式处理html
def getChoice(url):
    if re.match(r'https://.+\.zhihu\.com.*', url):
        return "zhihu"
    if re.match(r"https://.+\.wikipedia\.org.*", url):
        return "wikipedia"
    if re.match(r"https://.+\.jianshu\.com.*", url):
        return "imgAlt"
    # csdn并不一定使用katex，也可能是mathjax，但我没有办法处理mathjax，因此直接假定是katex了
    if re.match(r"https://.+\.csdn\.net.*", url):
        return "katex"
    mp = {"0": "katex", "1": "imgAlt"}
    print('输入你的选择：', mp)
    return mp[input()]


if __name__ == '__main__':
    # 获取剪切板数据
    s = copy.DumpHtml()
    # 获取来源网站的网址
    url = re.search(r'SourceURL:(.+)', s).group(1)
    choice = getChoice(url)
    # 获取html数据
    s = re.sub(r'.+<!--StartFragment-->(.+)<!--EndFragment-->.+', r"\1", s, flags=re.S)
    soup = BeautifulSoup(s, 'html.parser')
    locals()[choice](soup)
    pyperclip.copy(ans)
