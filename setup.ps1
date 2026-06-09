# Setup script: create venv, install dependencies
$venvPath = Join-Path $PSScriptRoot ".venv"

if (-not (Test-Path $venvPath)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Green
    python -m venv $venvPath
}

Write-Host "Activating virtual environment..." -ForegroundColor Green
& (Join-Path $venvPath "Scripts\Activate.ps1")

Write-Host "Installing dependencies..." -ForegroundColor Green
pip install -r (Join-Path $PSScriptRoot "requirements.txt")

Write-Host "Done!" -ForegroundColor Green
