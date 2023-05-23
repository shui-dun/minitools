import re

if __name__ == '__main__':
    s = '| 单词 | 释义 |\n|-----|-----|\n'
    with open('data/result.txt') as f:
        for line in f:
            line = re.sub(r'\t网络\t.*', '', line)
            line = re.sub(r'\t', '  ', line)
            line = line.split(maxsplit=1)
            print(line)
            line = '|{}|{}|'.format(line[0].strip(), line[1].strip())
            s += line + '\n'
    with open('data/result_v2.txt', 'w') as f:
        f.write(s)
