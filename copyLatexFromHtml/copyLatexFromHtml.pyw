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
    if '\\\\' in origin:
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
        except:
            pass
        return
    for child in soup.children:
        zhihu(child)


def getChoice(url):
    if re.match(r'https://www\.zhihu\.com/.*', url):
        return "zhihu"
    if re.match(r"https://.+\.wikipedia\.org.*", url):
        return "wikipedia"


if __name__ == '__main__':
    s = copy.DumpHtml()
    choice = getChoice(re.search(r'SourceURL:(.+)', s).group(1))
    s = re.sub(r'.+<!--StartFragment-->(.+)<!--EndFragment-->.+', r"\1", s, flags=re.S)
    soup = BeautifulSoup(s, 'html.parser')
    locals()[choice](soup)
    pyperclip.copy(ans)
