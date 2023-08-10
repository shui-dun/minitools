import psutil
from config import *
import os
import time
import re


def handlesOfProcess(processName):
    """
    根据进程名称（前缀），获得它所占有的所有文件
    """
    handles = set()
    pattern = re.compile(r"^\s*([0-9A-F]+):\s*([A-Za-z]+)\s+([^\s].+[^\s])$")
    output = os.popen('handle -a -p {}'.format(processName)).read()
    for line in output.split('\n'):
        if 'ALPC Port' in line:
            continue
        match = pattern.search(line)
        if match is not None:
            handles.add('{}\t\t{}'.format(match.group(2), match.group(3)))
    return handles


if __name__ == '__main__':
    handles = set()
    while True:
        time.sleep(interval)
        newHandles = handlesOfProcess(processName)
        for handle in (newHandles - handles):
            print(handle)
        handles |= newHandles

