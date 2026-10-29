@echo off
title Push to GitHub - SecureVote
color 0A
cd /d "%~dp0"

echo ===============================================================================
echo                Pushing SecureVote Monorepo to GitHub
echo                Repo: https://github.com/shanmugaprabhu2008-hub/Fingerprint-Project.git
echo ===============================================================================
echo.

set "PATH=C:\Users\SHANMUGAPRABHU\AppData\Local\GitHubDesktop\app-3.6.7\resources\app\git\cmd;%PATH%"

echo [*] Local Branch: main
echo [*] Remote URL:   https://github.com/shanmugaprabhu2008-hub/Fingerprint-Project.git
echo.
echo [*] Uploading all commits and files to GitHub...
echo.

git push -u origin main --force

if %ERRORLEVEL% equ 0 (
    echo.
    echo ===============================================================================
    echo [SUCCESS] All files successfully pushed to GitHub!
    echo.
    echo View repository online:
    echo https://github.com/shanmugaprabhu2008-hub/Fingerprint-Project
    echo ===============================================================================
) else (
    echo.
    echo ===============================================================================
    echo [!] Push failed or waiting for authentication.
    echo     If GitHub asks for authorization, please click 'Sign in with your browser'
    echo     or provide a Personal Access Token (PAT).
    echo ===============================================================================
)

echo.
pause
