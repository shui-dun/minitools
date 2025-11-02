import subprocess
import time
import os
from datetime import datetime, timedelta
from queue import PriorityQueue
import models
import const
from process_manager import kill_existing_process, save_current_pid
import wait_network

def run_command(cmd):
    # check=True, capture_output=True, text=True 是为了执行出错时能抛出异常（默认不抛出异常）
    # creationflags=subprocess.CREATE_NO_WINDOW 是为了在Windows下不弹出命令行窗口
    return subprocess.run(
        cmd,
        check=True,
        capture_output=True,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW
    ).stdout

def write_log(log_path, repo_path, level, msg):
    with open(log_path, "a", encoding="utf-8") as log_file:
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        log_file.write(f"{level}: [{timestamp}] {repo_path} - {msg}\n")

def process_repo(repo_config, log_path):
    try:
        os.chdir(repo_config.path)
        if not os.path.exists(".git"):
            run_command(["git", "init"])
            write_log(log_path, repo_config.path, "INFO", "初始化新的Git仓库")
        run_command(["git", "add", "."])
        commit_msg = f"Auto-commit at {time.strftime('%Y-%m-%d %H:%M:%S')}"
        run_command(["git", "commit", "-m", commit_msg])
        if repo_config.do_push:
            try:
                run_command(["git", "remote", "get-url", "origin"])
            except subprocess.CalledProcessError:
                repo_name = os.path.basename(repo_config.path)
                # 避免出现空格
                repo_name = repo_name.replace(" ", "_")
                origin_path = const.DEFAULT_ORIGIN_PREFIX + repo_name
                run_command(["git", "remote", "add", "origin", origin_path])
                write_log(log_path, repo_config.path, "INFO", f"设置ORIGIN：{origin_path}")
            run_command(["git", "push", "origin", "--all"]) # 推送所有分支
        write_log(log_path, repo_config.path, "INFO", f"成功提交更改: {commit_msg}")
    except subprocess.CalledProcessError as e:
        if 'nothing to commit, working tree clean' in e.stdout:
            write_log(log_path, repo_config.path, "INFO", "没有需要提交的更改")
        else:
            # 捕获详细的命令行错误输出
            err_msg = (
                f"执行命令 {e.cmd} 时发生错误，返回码为 {e.returncode}\n"
                f"标准输出: {e.stdout}\n"
                f"标准错误: {e.stderr}\n"
            )
            write_log(log_path, repo_config.path, "ERROR", err_msg)
    except Exception as e:
        err_msg = f"发生错误: {e}\n"
        write_log(log_path, repo_config.path, "ERROR", err_msg)

def run_scheduler(log_path):
    # 创建优先队列
    task_queue = PriorityQueue()
    
    # 初始化任务
    now = datetime.now()
    for config in const.REPO_CONFIGS:
        task = models.RepoTask(config=config, next_run=now)
        # 优先队列项格式：(下次运行时间的时间戳, 任务对象)
        task_queue.put(task)
   
    while True:
        # 获取最近要执行的任务
        task = task_queue.get()
        next_ts = task.next_run.timestamp()
        now = datetime.now()
        
        # 如果任务还没到执行时间，等待
        if next_ts > now.timestamp():
            sleep_time = next_ts - now.timestamp()
            time.sleep(sleep_time)
        
        # 执行任务
        process_repo(task.config, log_path)
        
        # 计算下次执行时间并重新加入队列
        task.next_run = datetime.now() + timedelta(minutes=task.config.interval_minutes)
        task_queue.put(task)

if __name__ == "__main__":
    # 检查并终止已存在的进程
    kill_existing_process()
    # 保存当前进程的PID
    save_current_pid()
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(script_dir, "commit.log")
    
    wait_network.wait_for_network()
    
    run_scheduler(log_path)
