import sys

# 将http消息头转化为python字典

if __name__ == '__main__':
    d = dict()
    with open(sys.argv[1]) as f:
        for l in f.readlines():
            pair = l.split(':', maxsplit=1)
            d[pair[0]] = pair[1].strip()
        print(d)
    with open(sys.argv[1], 'w') as f:
        f.write(str(d))
