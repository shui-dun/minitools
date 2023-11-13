import subprocess
import time

def run_command():
    command = 'wsl -d docker-desktop ash -c "echo 3 > /proc/sys/vm/drop_caches; sync"'
    subprocess.run(command, creationflags=subprocess.CREATE_NO_WINDOW)

def main():
    # 运行Docker Desktop.exe
    subprocess.run('"Docker Desktop.exe"', creationflags=subprocess.CREATE_NO_WINDOW)
    while True:
        try:
            time.sleep(180)  # 等待180秒，即3分钟
            run_command()
        except Exception as e:
            print(e)

if __name__ == "__main__":
    main()
