import subprocess
import time

def check_docker_desktop_running():
    try:
        # check_output会返回命令执行结果，如果命令执行失败则会抛出异常
        # text=True会将输出转换成字符串
        output = subprocess.check_output(["tasklist"], text=True, shell=True)
        return "Docker Desktop" in output
    except Exception as e:
        print(f"Error: {e}")
        return False

def run_command():
    commands = [
        "sync",
        "echo 3 | tee /proc/sys/vm/drop_caches",
        "echo 1 | tee /proc/sys/vm/compact_memory",
    ]
    for command in commands:
        full_command = f'wsl -d docker-desktop ash -c "{command}"'
        # print(full_command)
        subprocess.run(full_command, shell=True)

if __name__ == "__main__":
    while True:
        try:
            time.sleep(180)
            if check_docker_desktop_running():
                run_command()
        except Exception as e:
            print(e)
