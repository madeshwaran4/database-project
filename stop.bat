@echo off
title SecureVote - Stop Services
color 0C

echo ===============================================================================
echo                Stopping All SecureVote Services
echo ===============================================================================
echo.

echo [*] Terminating backend and frontend processes on ports 8000 and 3000...

for /f "tokens=5" %%a in ('netstat -aon ^| findstr /r ":8000\>" 2^>nul') do (
    taskkill /f /pid %%a >nul 2>&1
)

for /f "tokens=5" %%a in ('netstat -aon ^| findstr /r ":3000\>" 2^>nul') do (
    taskkill /f /pid %%a >nul 2>&1
)

taskkill /fi "WINDOWTITLE eq SecureVote - Backend Service*" /f >nul 2>&1
taskkill /fi "WINDOWTITLE eq SecureVote - Frontend Kiosk*" /f >nul 2>&1

echo [+] SecureVote services have been stopped.
echo.
timeout /t 2 /nobreak > nul
