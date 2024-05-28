# pipenvInstaller

指定一个pipenv项目中的的python文件，会自动安装项目所需的python环境，并为该文件创建快捷方式。

## 详细介绍

运行 `pipenv run python main.py`，并输入目标python文件 `/path/to/project_name/python_file.py` 的路径，效果如下：

- 找到与 `python_file.py` 关联的 pipfile 位置，安装 pipfile 中指定的 python 环境

- 在 `C:\ProgramData\Microsoft\Windows\Start Menu\Programs` 创建一个名为 `project_name.lnk` 的快捷方式，指向 `python_file.py`。具体来说：

  - 对于 `python_file.py`，会创建快捷方式指向 `/path/to/python.exe "/path/to/project_name/python_file.py"`，该 `python.exe` 位于虚拟环境中
  - 对于 `python_file.pyw`，会创建快捷方式指向 `/path/to/pythonw.exe "/path/to/project_name/python_file.pyw"`。

  之所以快捷方式的内容不是 `pipenv run python /path/to/project_name/python_file.py`，是因为寻找虚拟环境太耗时了。

- 同样地，在 `C:\Windows\System32` 下创建 `project_name.bat` 脚本