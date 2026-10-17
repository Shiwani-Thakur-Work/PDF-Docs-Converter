# DocFlow PowerShell Runner
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "       DocFlow - PDF & Docs Converter Server            " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

$VenvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "[INFO] Creating virtual environment..." -ForegroundColor Yellow
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        uv venv .venv --python 3.11
        & .\.venv\Scripts\activate.ps1
        uv pip install -r requirements.txt
    } else {
        python -m venv .venv
        & .\.venv\Scripts\activate.ps1
        pip install -r requirements.txt
    }
}

Write-Host "[INFO] Launching DocFlow at http://localhost:8000" -ForegroundColor Green
Start-Process "http://localhost:8000"
& $VenvPython -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
