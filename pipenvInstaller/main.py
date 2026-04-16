import os
import sys
import subprocess
import win32com.client
from elevate import elevate
import ctypes
import traceback
import shutil

def get_pipenv_cmd():
    """获取系统中 pipenv 的绝对执行路径"""
    pipenv_path = shutil.which('pipenv')
    if not pipenv_path:
        print("致命错误：无法在系统环境变量中找到 pipenv。")
        exit(1)
    return pipenv_path

def my_exception_handler(exc_type, exc_value, exc_traceback):
    # 1. 打印标准的 Traceback 信息
    traceback.print_exception(exc_type, exc_value, exc_traceback)
    
    # 2. 阻止窗口立即关闭
    print("\n" + "="*30)
    input("程序崩溃了！请检查上方堆栈信息。按回车键退出...")

def is_admin():
    """检查当前用户是否具有管理员权限"""
    try:
        # Only Windows Vista and newer support the isUserAnAdmin API
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def find_pipenv_venv(python_file):
    """在指定Python文件目录中查找并返回虚拟环境路径"""
    try:
        result = subprocess.check_output([get_pipenv_cmd(), '--venv'], cwd=os.path.dirname(python_file))
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
    """在开始菜单创建快捷方式"""
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
    subprocess.check_call([get_pipenv_cmd(), 'install'], cwd=project_path)

def create_bat_file(interpreter_path, python_file, bat_file_path):
    """创建批处理文件来运行指定的Python脚本"""
    with open(bat_file_path, 'w') as bat_file:
        bat_file.write(f'@echo off\n"{interpreter_path}" {python_file} %*\n')

def exit(retVal=0):
    if interactive:
        input('Press Enter to exit...')
    sys.exit(retVal)

if __name__ == "__main__":
    # 将全局异常处理器设置为我们自定义的函数
    sys.excepthook = my_exception_handler

    if not is_admin():
        elevate(show_console=True)  # 这会提高权限并重启脚本

    # 是否是交互形式
    interactive = len(sys.argv) == 1

    # 获得目标Python文件路径
    python_file = sys.argv[1] if (not interactive) else input('请输入python文件的路径：')

    # 删除引号
    python_file = python_file.strip('"')

    # 判断目标文件是否存在
    if not os.path.exists(python_file):
        print('指定的Python文件不存在')
        exit(1)

    # 得到完整路径
    python_file = os.path.abspath(python_file)

    find_project, project_path = find_pipfile_in_path(os.path.dirname(python_file))

    if not find_project:
        print('Could not find Pipfile in path')
        exit(1)
    else:
        create_venv(project_path)

    project_name = os.path.basename(project_path)

    venv_path = find_pipenv_venv(python_file)
    
    if not venv_path:
        print('Could not find pipenv virtual environment for', python_file)
        exit(1)        

    interpreter = 'pythonw.exe' if python_file.endswith('.pyw') else 'python.exe'
    interpreter_path = os.path.join(venv_path, 'Scripts', interpreter)

    destination = r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs"
    shortcut_name = os.path.join(destination, project_name + ".lnk")
    print(f'Creating shortcut for {interpreter_path} {python_file} at {shortcut_name}')
    create_shortcut(interpreter_path, f'"{python_file}"', shortcut_name)

    bat_file_path = os.path.join('C:\\Windows\\System32', project_name + '.bat')
    print(f'Creating BAT file at {bat_file_path}')
    create_bat_file(interpreter_path, f'"{python_file}"', bat_file_path)

    exit(0)