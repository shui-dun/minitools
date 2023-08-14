@echo off
REM %~dp0表示当前bat文件所在路径，而非工作目录
python "%~dp0pipenvRun.py" %*
