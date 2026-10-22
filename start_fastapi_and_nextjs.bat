@echo off
title Launch PARIVESH 2.0 KYA (FastAPI + Next.js)
color 0B

echo ==============================================================
echo    PARIVESH 2.0 KYA - ENTERPRISE PRODUCTION STACK LAUNCHER
echo    Backend: FastAPI (Port 8000)
echo    Frontend: Next.js (Port 3000)
echo ==============================================================
echo.

:: 1. Launch FastAPI Backend in a separate window
echo [*] Launching FastAPI Backend Service...
start "PARIVESH Backend (FastAPI)" cmd /k "call venv\Scripts\activate.bat && python backend/run.py"

:: 2. Wait 3 seconds for backend to initialize
timeout /t 3 /nobreak >nul

:: 3. Launch Next.js Frontend in a separate window
echo [*] Launching Next.js Frontend (Vercel Stack)...
start "PARIVESH Frontend (Next.js)" cmd /k "cd frontend && npm run dev"

:: 4. Open browser
echo.
echo [*] Opening application at http://localhost:3000 ...
timeout /t 2 /nobreak >nul
start http://localhost:3000

echo.
echo ==============================================================
echo    Stack is active!
echo    - Frontend:  http://localhost:3000
echo    - API Docs:  http://127.0.0.1:8000/docs
echo ==============================================================
