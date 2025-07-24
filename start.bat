@echo off
set PYTHON_HOME=%~dp0env
set PATH=%PYTHON_HOME%;%PYTHON_HOME%\Scripts;%PATH%
"%PYTHON_HOME%\python.exe" "%~dp0main.py"
pause