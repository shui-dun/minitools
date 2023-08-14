# pipenvRun

在windows上一键使用pipenv运行python文件

## 文件功能

- *pipenv_run_python.vbs* 表示使用pipenv运行python文件，但不显示控制台
- *pipenv_run_python_with_console.bat* 表示使用pipenv运行python文件，同时显示控制台

## 使用方法

1. 创建 *pipenv_run_python.vbs* 和 *pipenv_run_python_with_console.bat* 的快捷方式

1. 按下 Windows + R 键，输入 shell:sendto 并按 `Enter`。

1. 将上述的两个快捷方式移动到打开的文件夹中

1. 在任意文件夹中，右键点击要运行的python文件，选择 `发送到` -> `pipenv_run_python` 或 `pipenv_run_python_with_console`