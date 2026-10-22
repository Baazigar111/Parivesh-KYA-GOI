@echo off
title PARIVESH KYA - FastAPI Backend Service (Port 8000)
color 0A

echo ==============================================================
echo    PARIVESH 2.0 KYA - ENTERPRISE FASTAPI BACKEND SERVICE
echo ==============================================================
echo.

if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found in .\venv
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo [*] Starting FastAPI with Uvicorn on http://127.0.0.1:8000 ...
echo [*] Interactive Swagger UI: http://127.0.0.1:8000/docs
echo [*] Redoc API Reference: http://127.0.0.1:8000/redoc
echo.

python backend/run.py

pause
