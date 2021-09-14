import re
import pyperclip
from bs4 import BeautifulSoup
import copy

ans = ""


def wikipedia(soup):
    global ans
    if not hasattr(soup, "children"):
        ans += soup
        return
    if soup.name == "img":
        try:
            ans += " ${}$ ".format(re.sub('\r|\n|(\r\n)|\s', ' ', soup['alt']).strip())
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
            ans += " ${}$ ".format(re.sub('\r|\n|(\r\n)|\s', ' ', soup['data-formula']).strip())
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
