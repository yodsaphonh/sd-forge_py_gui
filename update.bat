@echo off
setlocal

cd /d "%~dp0"

if exist ".git" (
    echo Updating repository...
    git pull --ff-only
    if errorlevel 1 (
        echo Failed to update repository.
        exit /b 1
    )
) else (
    echo No git repository detected. Skipping source update.
)

rem Prefer a local virtual environment when installing dependencies
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

echo Installing Python dependencies...
"%PYTHON_EXE%" -m pip install --upgrade -r requirements.txt
if errorlevel 1 (
    echo Dependency installation failed.
    exit /b 1
)

echo Update complete.
endlocal
