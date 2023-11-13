import subprocess
import time

def run_command():
    command = 'wsl -d docker-desktop ash -c "echo 3 > /proc/sys/vm/drop_caches; sync"'
    subprocess.run(command, creationflags=subprocess.CREATE_NO_WINDOW)

def main():
    while True:
        run_command()
        time.sleep(180)  # 等待180秒，即3分钟

if __name__ == "__main__":
    main()
