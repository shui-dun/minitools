import re
import pyperclip
from bs4 import BeautifulSoup
import copy

ans = ""


def handleLatex(origin):
    if origin is None or origin == "":
        return ""
    origin = origin.strip()
    origin = re.sub(r'\s+', ' ', origin)
    origin = re.sub(r'\\\\ *', r'\\\\\r\n', origin)
    if '\\\\' in origin or len(origin) > 32:
        return '\r\n\r\n$$\r\n{}\r\n$$\r\n\r\n'.format(origin)
    else:
        return ' ${}$ '.format(origin)


def wikipedia(soup):
    global ans
    if not hasattr(soup, "children"):
        ans += soup
        return
    if soup.name == "img":
        try:
            ans += handleLatex(soup['alt'])
        except:
            pass
        return
    if soup.name == "annotation":
        return
    for child in soup.children:
        wikipedia(child)


def zhihu(soup):
    global ans
    if not hasattr(soup, "children"):
        ans += soup
        return
    if soup.name == "img":
        try:
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
            ans += handleLatex(soup['alt'])
        except Exception as e:
            print(e)
        return
    for child in soup.children:
        imgAlt(child)


def getChoice(url):
    if re.match(r'https://www\.zhihu\.com/.*', url):
        return "zhihu"
    if re.match(r"https://.+\.wikipedia\.org.*", url):
        return "wikipedia"
    if re.match(r'https://.*csdn\..*', url):
        return "katex"
    if re.match(r"https://www\.jianshu\.com/.*", url):
        return "imgAlt"
    return "katex"


if __name__ == '__main__':
    s = copy.DumpHtml()
    try:
        choice = getChoice(re.search(r'SourceURL:(.+)', s).group(1))
    except Exception as e:
        print(e)
        choice = "normal"
    s = re.sub(r'.+<!--StartFragment-->(.+)<!--EndFragment-->.+', r"\1", s, flags=re.S)
    soup = BeautifulSoup(s, 'html.parser')
    locals()[choice](soup)
    pyperclip.copy(ans)
