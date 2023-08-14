import sys
import os
import subprocess

def find_pipfile_in_path(path):
    """
    检查给定路径或其上级路径中是否存在Pipfile
    """
    current_path = path
    while current_path != os.path.dirname(current_path):  # 判断是否已到达根目录
        if os.path.exists(os.path.join(current_path, 'Pipfile')):
            return True
        current_path = os.path.dirname(current_path)
    return False

def main():
    if len(sys.argv) < 2:
        print("请提供一个Python文件来执行.")
        sys.exit(1)
    
    python_script = sys.argv[1]

    if not os.path.exists(python_script):
        print(f"提供的文件 {python_script} 不存在.")
        sys.exit(1)
    
    if find_pipfile_in_path(os.path.dirname(os.path.abspath(python_script))):
        cmd_prefix = ["pipenv", "run", "python.exe"]
    else:
        cmd_prefix = ["python.exe"]

    # 对于.pyw文件，我们要隐藏控制台
    # 使用subprocess.CREATE_NO_WINDOW来避免创建新的控制台窗口
    if python_script.endswith('.pyw'):
        subprocess.Popen(cmd_prefix + [python_script], creationflags=subprocess.CREATE_NO_WINDOW)
    else:
        subprocess.Popen(cmd_prefix + [python_script])

if __name__ == "__main__":
    main()
