@echo off
setlocal

cd /d "%~dp0"

rem Prefer a local virtual environment if available
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

"%PYTHON_EXE%" main.py %*

endlocal
