import os
import sys
import subprocess
import win32com.client
from elevate import elevate
import ctypes
import shutil

def is_admin():
    try:
        # Only Windows Vista and newer support the isUserAnAdmin API, so we'll check the OS version
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def find_pipenv_venv(python_file):
    try:
        result = subprocess.check_output(['pipenv', '--venv'], cwd=os.path.dirname(python_file))
        return result.decode().strip()
    except:
        return None
    
def find_pipfile_in_path(path):
    """
    检查给定路径或其上级路径中是否存在Pipfile，返回是否找到以及项目路径（即存在Pipfile的目录名）
    """
    current_path = path
    while current_path != os.path.dirname(current_path):  # 判断是否已到达根目录
        if os.path.exists(os.path.join(current_path, 'Pipfile')):
            return (True, current_path)
        current_path = os.path.dirname(current_path)
    return (False, '')

def create_shortcut(target, arguments, shortcut_name, start_dir=''):
    shell = win32com.client.Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(shortcut_name)
    shortcut.TargetPath = target
    shortcut.Arguments = arguments
    shortcut.WorkingDirectory = start_dir
    shortcut.save()

def create_venv(project_path):
    """
    在给定路径中创建虚拟环境
    """
    subprocess.check_call(['pipenv', 'install'], cwd=project_path)


def main():
    if not is_admin():
        elevate(show_console=True)  # 这会提高权限并重启脚本

    python_file = input('请输入python文件的路径：')
    # 删除引号
    python_file = python_file.strip('"')

    find_project, project_path = find_pipfile_in_path(os.path.dirname(python_file))

    if not find_project:
        print('Could not find Pipfile in path')
        input('Press Enter to exit...')
        sys.exit(1)
    else:
        create_venv(project_path)

    project_name = os.path.basename(project_path)

    venv_path = find_pipenv_venv(python_file)
    
    if not venv_path:
        print('Could not find pipenv virtual environment for', python_file)
        input('Press Enter to exit...')
        sys.exit(1)

    interpreter = 'pythonw.exe' if python_file.endswith('.pyw') else 'python.exe'
    interpreter_path = os.path.join(venv_path, 'Scripts', interpreter)

    destination = r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs"

    shortcut_name = os.path.join(destination, project_name + ".lnk")

    print(f'Creating shortcut for {interpreter_path} {python_file} at {shortcut_name}')

    create_shortcut(interpreter_path, f'"{python_file}"', shortcut_name)

    input('Press Enter to exit...')

if __name__ == "__main__":
    main()