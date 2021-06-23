import pyperclip
import re

s = pyperclip.paste()
pyperclip.copy('[填空]({}) '.format(re.sub('\s+', '_', s.strip())))
