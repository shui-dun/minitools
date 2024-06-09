import os
import datetime

def adjust_date(date_str):
    """将日期转换为 YYYY-MM-DD 格式"""
    date = datetime.datetime.strptime(date_str, "%Y年%m月%d日")
    return date.strftime("%Y-%m-%d")

def process_file(file_path):
    """处理单个文件"""
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    new_lines = [adjust_date(line.strip()) + '\n' for line in lines]
    
    with open(file_path, 'w', encoding='utf-8') as file:
        file.writelines(new_lines)

def process_all_txt_files():
    """处理当前目录下所有的 .txt 文件"""
    for file_name in os.listdir():
        if file_name.endswith('.txt'):
            process_file(file_name)
            print(f"文件 {file_name} 已处理完成。")

process_all_txt_files()
print("所有文件已处理完成。")
