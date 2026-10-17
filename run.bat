@echo off
setlocal
cd /d "%~dp0"
title DocFlow - PDF & Docs Converter

echo ========================================================
echo        DocFlow - PDF & Docs Converter Server
echo ========================================================

REM Check if .venv exists
if not exist ".venv\Scripts\python.exe" (
    echo [INFO] Virtual environment not found. Setting up with uv/python...
    where uv >nul 2>&1
    if %errorlevel% equ 0 (
        uv venv .venv --python 3.11
        call .venv\Scripts\activate.bat
        uv pip install -r requirements.txt
    ) else (
        python -m venv .venv
        call .venv\Scripts\activate.bat
        pip install -r requirements.txt
    )
) else (
    call .venv\Scripts\activate.bat
)

echo [INFO] Starting DocFlow server on http://localhost:8000 ...
start http://localhost:8000
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
pause
