import os
import signal
import sys
import subprocess

pid_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'auto_commit.pid')

def kill_existing_process():
    """
    检查并终止已存在的auto_commit进程
    返回True如果成功终止了现有进程，False如果失败，例如没有找到现有进程
    """
    try:
        # 检查PID文件是否存在
        if not os.path.exists(pid_file):
            print("PID文件不存在，无法终止现有进程")
            return False
        # 读取PID文件中的PID
        with open(pid_file, 'r') as f:
            old_pid = int(f.read().strip())
        # 检查旧进程是否是auto_commit
        if 'auto_commit.py' not in get_specific_process_cmdline(old_pid):
            print(f"旧进程不存在或者不是auto_commit.py，PID: {old_pid}")
            return False
        # 终止现有进程
        os.kill(old_pid, signal.SIGTERM)
        return True
    except Exception as e:
        print(f"无法终止现有进程: {e}")
        return False

def save_current_pid():
    """
    保存当前进程的PID到文件
    """
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))
        
def get_specific_process_cmdline(pid):
    """获取指定PID的命令行参数，不依赖psutil等第三方库"""
    try:
        if sys.platform.startswith('win'):
            cmd = f'wmic process where processid={pid} get commandline'
            result = subprocess.run(cmd.split(), capture_output=True, text=True, encoding='gbk', creationflags=subprocess.CREATE_NO_WINDOW)
            # 去掉第一行（标题行）并清理空格
            lines = result.stdout.strip().split('\n')
            return '\n'.join(line.strip() for line in lines[1:] if line.strip())
        else:
            # Linux/Mac
            with open(f'/proc/{pid}/cmdline', 'r') as f:
                return f.read().replace('\0', ' ').strip() # cmdline 里面 空格是 \0 分隔的，所以需要替换成空格
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    # 测试 get_specific_process_cmdline
    print(get_specific_process_cmdline(os.getpid()))