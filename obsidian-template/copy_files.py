import shutil
import os
import stat

# 文件夹设置，为了方便，硬编码在这里
source_folder = r"D:\file\cloud\note"
dest_folder = os.path.join(os.path.dirname(__file__), "vault")
include_folders = [
    r"计划\计划.md",
    r"计划\super-task-view.md",
    r"note\note.md",
    r"note\note-eof.md",
    r"job\job.md",
    r"habit\habit.md",
    r"habit\clock-info.md",
    r"misc\customjs",
    r"misc\dataview-scripts",
    r"misc\front-matter-template",
    r"misc\template",
]

if __name__ == "__main__":
    # 删除并创建目标文件夹
    if os.path.exists(dest_folder):
        # 修复 PermissionError: [WinError 5] 拒绝访问 的问题
        def delete(func, path, execinfo):
            os.chmod(path, stat.S_IWUSR)
            func(path)
        shutil.rmtree(dest_folder, onerror=delete)
    os.makedirs(dest_folder, exist_ok=True)
    
    # 复制指定的文件和文件夹
    for item in include_folders:
        src_path = os.path.join(source_folder, item)
        dest_path = os.path.join(dest_folder, item)
        # print(f"复制: {src_path} -> {dest_path}")
        
        if os.path.isdir(src_path):
            shutil.copytree(src_path, dest_path)
        elif os.path.isfile(src_path):
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            shutil.copy2(src_path, dest_path)
        else:
            print(f"路径不存在: {src_path}")

    print("文件复制完成")
