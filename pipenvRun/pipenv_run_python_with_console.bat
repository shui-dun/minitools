@echo off
cd /d %~dp1
pipenv run python %~nx1
pause
