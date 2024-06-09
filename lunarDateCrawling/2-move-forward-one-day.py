"""
将北方小年转化为南方小年
"""

import datetime

def adjust_date(date_str):
    """将日期向后挪一天"""
    date = datetime.datetime.strptime(date_str, "%Y年%m月%d日")
    new_date = date + datetime.timedelta(days=1)
    return new_date.strftime("%Y年%m月%d日")

def process_file(file_path):
    """处理文件"""
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    new_lines = [adjust_date(line.strip()) + '\n' for line in lines]
    
    with open(file_path, 'w', encoding='utf-8') as file:
        file.writelines(new_lines)

process_file("xiaonian.txt")
