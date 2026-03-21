@echo off
title Manpower Payroll System
color 1F
cls
echo ==========================================
echo    MANPOWER PAYROLL SYSTEM
echo ==========================================
echo.
cd /d "C:\Users\Lenovo\manpower_payroll"
call "C:\Users\Lenovo\manpower_payroll\venv\Scripts\activate.bat"

echo [1/2] Starting Flask App...
start "Manpower Flask" cmd /k "python run.py"

echo Waiting for Flask to start...
timeout /t 5 /nobreak > nul

echo [2/2] Starting Cloudflare Tunnel...
start "Cloudflare Tunnel" cmd /k "cloudflared tunnel --url http://localhost:5000"

echo Opening Local Browser...
timeout /t 3 /nobreak > nul
start "" "http://127.0.0.1:5000"

echo.
echo ==========================================
echo  PC     : http://127.0.0.1:5000
echo  Mobile : Check Cloudflare Tunnel window
echo           for the https URL
echo ==========================================
pause
