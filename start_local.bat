@echo off
title PARIVESH 2.0 KYA - Local Hosting Launcher
echo ==============================================================================
echo       PARIVESH 2.0 KYA - Local Dual-Stack Server Launcher
echo ==============================================================================
echo.

cd /d "%~dp0"

echo [1/2] Launching FastAPI Backend on http://localhost:8000 ...
start "PARIVESH Backend (FastAPI)" cmd /k ".\venv\Scripts\python.exe backend/run.py"

timeout /t 3 /nobreak >nul

echo [2/2] Launching Next.js Frontend on http://localhost:3000 ...
start "PARIVESH Frontend (Next.js)" cmd /k "cd frontend && npm run dev"

echo.
echo ==============================================================================
echo   Services are starting in separate windows:
echo   - Backend API:    http://localhost:8000
echo   - Swagger Docs:   http://localhost:8000/docs
echo   - Frontend UI:    http://localhost:3000
echo ==============================================================================
echo.
pause
