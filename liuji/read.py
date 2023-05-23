import re


def readLiuJi():
    result = set()
    with open('data/liuji.txt') as f:
        for line in f:
            striped = line.strip()
            striped = re.sub(r'\/.*', '', striped)
            striped = re.sub(r"'", '', striped)
            striped = re.sub(r"\d+$", "", striped)
            striped = re.sub(r"\(.*\)", "", striped)
            striped = re.sub(r"\s+", "", striped)
            if ')' in striped or '(' in striped:
                continue
            result.add(striped)
    result.remove('')
    result.remove('高教')
    result.remove('-sation')
    result.remove('-sational')
    result.remove('-xion')
    result.remove('fly!')
    result.remove('check2')
    return result


def readKaoYan1():
    result = set()
    with open('data/kaoyan1.txt') as f:
        isNext = False
        for line in f:
            striped = line[:-1]
            if isNext:
                striped = re.sub(r'\/.*', '', striped)
                striped = re.sub(r"\(.*\)", "", striped)
                result.add(striped)
                isNext = False
                continue
            if striped.isdigit():
                isNext = True
                continue
    result.remove('memo（=memorandum）')
    return result


def readKaoYan2():
    result = set()
    with open('data/kaoyan2.txt') as f:
        for line in f:
            striped = line.strip()
            if not striped.encode('UTF-8').isalpha():
                continue
            result.add(striped)
    return result


def readKaoYan3():
    result = set()
    with open('data/kaoyan3.txt') as f:
        for line in f:
            split = line.split()
            striped = ''
            if len(split) == 2 and split[0].isdigit():
                striped = split[1]
            elif len(split) == 1 and split[0].encode('UTF-8').isalpha():
                striped = split[0]
            else:
                continue
            striped = re.sub(r'\/.*', '', striped)
            striped = re.sub(r"(\(|（).*(\)|）)", "", striped)
            result.add(striped)
    return result


def readKaoYan():
    s1 = readKaoYan1()
    s2 = readKaoYan2()
    s3 = readKaoYan3()
    s = s1 | s2 | s3
    return s

def is_contains_chinese(strs):
    for _char in strs:
        if '\u4e00' <= _char <= '\u9fa5':
            return True
    return False

def readGaoZhong():
    result = set()
    with open('data/gaozhong.txt') as f:
        for line in f:
            split = line.split()
            if len(split) == 1:
                continue
            striped = split[1]
            striped = re.sub(r"\[.+\]","", striped)
            striped = re.sub(r"\(.+\)", "", striped)
            striped = re.sub(r'\/.*', '', striped)
            striped = re.sub(r'（.*）', "", striped)
            striped = re.sub(r'[\[\(（=ˈ\*].*$', "", striped)
            if is_contains_chinese(striped):
                continue
            result.add(striped)
    result.remove('')
    result.remove('ａ.m.')
    result.remove('get--together')
    return result


def check(result):
    for i in result:
        if not i.encode('UTF-8').isalpha():
            print(i)


def finalResult():
    liuJi = readLiuJi()
    kaoYan = readKaoYan()
    gaoZhong = readGaoZhong()
    result = liuJi - kaoYan - gaoZhong
    result = list(result)
    result.sort()
    return result

if __name__ == '__main__':
    r = finalResult()
    print(r)