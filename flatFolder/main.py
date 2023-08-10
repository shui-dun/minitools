import os
from settings import *

def concat_files_in_folder(root_dir, output_file_name):
    with open(output_file_name, 'w') as output_file:
        for dirpath, dirnames, filenames in os.walk(root_dir):
            # Remove excluded folders from dirnames in-place
            for excluded in excludeFolders:
                if excluded in dirnames:
                    dirnames.remove(excluded)

            # 只允许指定的文件类型
            filenames = [filename for filename in filenames if filename.split('.')[-1] in allowFileTypes]

            # 排除指定的文件
            filenames = [filename for filename in filenames if filename not in excludeFiles]

            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                relative_filepath = os.path.relpath(filepath, root_dir)
                prompt = f'File [{relative_filepath}]:\n\n'
                
                output_file.write(prompt)
                
                with open(filepath, 'r', errors='replace') as current_file:
                    content = current_file.read()
                    output_file.write(content + '\n\n')

if __name__ == '__main__':    
    concat_files_in_folder(rootFolder, 'merged_file.txt')
