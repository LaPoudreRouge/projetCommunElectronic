@echo off
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

echo Installing dependencies...
.venv\Scripts\pip.exe install -r requirements.txt

echo Done!
