@echo off
if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found. Run setup.bat first.
    exit /b 1
)

echo Starting audio capture...
.venv\Scripts\python.exe receive.py %*
if errorlevel 1 pause
