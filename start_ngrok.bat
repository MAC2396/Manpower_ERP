@echo off
title Ngrok Tunnel
cd /d "C:\Users\Lenovo\manpower_payroll"
echo Starting Ngrok tunnel on port 5000...
ngrok http 5000
pause
