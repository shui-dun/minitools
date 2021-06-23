import re
import pyperclip

# 将markdown中的粗体字变为链接
# 例如，将 **hello** 变为 [填空](hello)
# 这样便于复习和考察
if __name__ == '__main__':
    md = pyperclip.paste()
    md = re.sub(r'\*\*(.+?)\*\*', lambda m: '[填空]({})'.format(m.group(1)), md)
    pyperclip.copy(md)
