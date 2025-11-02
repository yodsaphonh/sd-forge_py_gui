@echo off
setlocal enabledelayedexpansion

REM --- ไปที่โฟลเดอร์ไฟล์นี้อยู่ ---
cd /d "%~dp0"

REM --- เลือกตัวเรียก Python ---
set PY=python
where py >nul 2>nul && set PY=py

REM --- สร้าง venv ถ้ายังไม่มี ---
if not exist ".venv\Scripts\python.exe" (
  echo [setup] creating venv...
  %PY% -3 -m venv .venv || goto :error
)

REM --- เข้า venv ---
call ".venv\Scripts\activate.bat" || goto :error

REM --- ติดตั้ง requirements ถ้ามีไฟล์ ---
if exist requirements.txt (
  echo [setup] installing requirements...
  python -m pip install --upgrade pip >nul
  pip install -r requirements.txt || goto :error
)

REM --- กำหนดพอร์ต API ของ Forge/A1111 (แก้ได้ตามเครื่องพี่) ---
set SD_API_BASE=http://127.0.0.1:7860

REM --- รันแอป ---
echo [run] starting app...
python main.py
set EXITCODE=%ERRORLEVEL%

REM --- ออกจาก venv ---
call ".venv\Scripts\deactivate.bat" >nul 2>nul

echo.
echo [done] exit code %EXITCODE%
pause
exit /b %EXITCODE%

:error
echo.
echo [ERROR] setup failed. Check messages above.
pause
exit /b 1
