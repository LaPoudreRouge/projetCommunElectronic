# Launch script: activate venv and run receive.py
$venvPath = Join-Path $PSScriptRoot ".venv"
$scriptPath = Join-Path $PSScriptRoot "receive.py"

if (-not (Test-Path $venvPath)) {
    Write-Host "Virtual environment not found. Run setup.ps1 first." -ForegroundColor Red
    exit 1
}

$python = Join-Path $venvPath "Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Host "Python executable not found in venv." -ForegroundColor Red
    exit 1
}

Write-Host "Starting audio capture..." -ForegroundColor Green
& $python $scriptPath @args
