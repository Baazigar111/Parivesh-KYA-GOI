# ==============================================================================
# PARIVESH 2.0 KYA - PowerShell Local Launcher
# ==============================================================================
$ErrorActionPreference = "Stop"

Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host "       PARIVESH 2.0 KYA - Local Dual-Stack Server Launcher" -ForegroundColor Cyan
Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host ""

$root = $PSScriptRoot

Write-Host "[1/2] Launching FastAPI Backend on http://localhost:8000 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root'; .\venv\Scripts\python.exe backend/run.py"

Start-Sleep -Seconds 3

Write-Host "[2/2] Launching Next.js Frontend on http://localhost:3000 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\frontend'; npm run dev"

Write-Host ""
Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host "  Services launched in background windows:" -ForegroundColor Yellow
Write-Host "  - Backend API:    http://localhost:8000" -ForegroundColor White
Write-Host "  - Swagger Docs:   http://localhost:8000/docs" -ForegroundColor White
Write-Host "  - Frontend UI:    http://localhost:3000" -ForegroundColor White
Write-Host "==============================================================================" -ForegroundColor Cyan
