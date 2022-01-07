import pyperclip
import json

if __name__ == '__main__':
    d = dict()
    for l in pyperclip.paste().splitlines():
        pair = l.split(':', maxsplit=1)
        d[pair[0]] = pair[1].strip()
    pyperclip.copy(json.dumps(d, indent=4))
