@echo off
title Push to GitHub - SecureVote
color 0A
cd /d "%~dp0"

echo ===============================================================================
echo                Pushing Database Project to GitHub
echo                Repo: https://github.com/madeshwarn4/database-project.git
echo ===============================================================================
echo.

echo [*] Local Branch: main
echo [*] Remote URL:   https://github.com/madeshwarn4/database-project.git
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
    echo https://github.com/madeshwarn4/database-project
    echo ===============================================================================
) else (
    echo.
    echo ===============================================================================
    echo [!] Push failed or waiting for authentication.
    echo     If GitHub asks for authorization, please sign in with your browser
    echo     or enter your GitHub Personal Access Token (PAT).
    echo ===============================================================================
)

echo.
pause
