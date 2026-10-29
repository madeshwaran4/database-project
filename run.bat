@echo off
setlocal enabledelayedexpansion
title SecureVote - System Controller
color 0B

:: Ensure working directory is always the script folder
cd /d "%~dp0"

echo ===============================================================================
echo                SecureVote Biometric Duplicate-Vote Prevention
echo                Database: Oracle 21c XE (python-oracledb thin mode)
echo ===============================================================================
echo.

:: -------------------------------------------------------------------------------
:: 1. Backend Pre-flight Checks
:: -------------------------------------------------------------------------------
echo [*] Checking Backend environment...

if not exist "backend\.env" (
    echo     [+] backend\.env not found. Creating from .env.example...
    if exist "backend\.env.example" (
        copy "backend\.env.example" "backend\.env" > nul
        echo     [!] IMPORTANT: Edit backend\.env and set your ORACLE_PASSWORD before starting!
    )
)

if not exist "backend\.venv\Scripts\python.exe" (
    echo     [!] Python virtual environment not found in backend\.venv
    echo     [*] Attempting to create virtual environment...
    py -3.14 -m venv backend\.venv 2>nul || py -3 -m venv backend\.venv 2>nul || python -m venv backend\.venv 2>nul
    if not exist "backend\.venv\Scripts\python.exe" (
        echo     [ERROR] Failed to create Python virtual environment. Please install Python 3.12+ and retry.
        pause
        exit /b 1
    )
    echo     [*] Installing backend dependencies from requirements.txt...
    backend\.venv\Scripts\pip.exe install -r backend\requirements.txt
)

:: -------------------------------------------------------------------------------
:: 2. Oracle Database Connectivity Check
:: -------------------------------------------------------------------------------
echo [*] Checking Oracle database connectivity...
pushd "%~dp0backend"
.venv\Scripts\python.exe -c "import oracledb; from app.core.config import settings; c = oracledb.connect(user=settings.ORACLE_USER, password=settings.ORACLE_PASSWORD, host=settings.ORACLE_HOST, port=settings.ORACLE_PORT, service_name=settings.ORACLE_SERVICE_NAME); print(f'    [+] Oracle {c.version} connected successfully'); c.close()"
set ORACLE_ERR=!ERRORLEVEL!
popd

if !ORACLE_ERR! neq 0 (
    echo     [!] Cannot connect to Oracle 21c XE.
    echo.
    echo     Possible fixes:
    echo       1. Start Oracle XE service: services.msc ^> OracleServiceXE ^> Start
    echo       2. Update backend\.env with correct ORACLE_PASSWORD
    echo       3. Run setup: cd backend ^&^& .venv\Scripts\python.exe db\setup_oracle_db.py
    echo.
    set /p CONTINUE="Continue anyway? [Y/N]: "
    if /i "!CONTINUE!" neq "Y" (
        exit /b 1
    )
)

:: -------------------------------------------------------------------------------
:: 3. Frontend Pre-flight Checks
:: -------------------------------------------------------------------------------
echo [*] Checking Frontend environment...

if not exist "frontend\node_modules" (
    echo     [!] Frontend node_modules not found.
    echo     [*] Running npm install - this may take a minute...
    cd /d "%~dp0frontend"
    call npm.cmd install
    cd /d "%~dp0"
)
echo     [+] Frontend ready.

:: -------------------------------------------------------------------------------
:: 4. Terminate Any Stale Instances on Ports 8000 and 3000
:: -------------------------------------------------------------------------------
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000"') do (
    if "%%a" neq "0" taskkill /f /pid %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3000"') do (
    if "%%a" neq "0" taskkill /f /pid %%a >nul 2>&1
)

:: -------------------------------------------------------------------------------
:: 5. Launch Services in Independent Titled Windows
:: -------------------------------------------------------------------------------
echo.
echo [*] [1/2] Starting FastAPI Backend on http://127.0.0.1:8000 ...
start "SecureVote - Backend Service (Port 8000)" /d "%~dp0backend" cmd /k "title SecureVote Backend (Port 8000) && color 0A && .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

echo [*] [2/2] Starting Next.js Frontend on http://localhost:3000 ...
start "SecureVote - Frontend Kiosk (Port 3000)" /d "%~dp0frontend" cmd /k "title SecureVote Frontend (Port 3000) && color 03 && npm.cmd run dev"

echo.
echo [*] Waiting 3 seconds for services to initialize...
timeout /t 3 /nobreak > nul

:: Auto-launch default browser
echo [*] Opening SecureVote web application in your default browser...
start http://localhost:3000

:: -------------------------------------------------------------------------------
:: 6. Interactive Control Console
:: -------------------------------------------------------------------------------
:MENU
cls
echo ===============================================================================
echo                SecureVote System Controller - Services Running
echo                Database: Oracle 21c XE ^| Backend: FastAPI + python-oracledb
echo ===============================================================================
echo.
echo   SERVICES ACTIVE:
echo     [Frontend Kiosk]   http://localhost:3000
echo     [Staff Login]      http://localhost:3000/login
echo     [Voting Booth]     http://localhost:3000/booth
echo     [Admin Dashboard]  http://localhost:3000/admin
echo     [API Documentation]http://127.0.0.1:8000/docs
echo     [Health Check]     http://127.0.0.1:8000/health
echo.
echo   DEMO CREDENTIALS:
echo     Administrator:     admin    /  admin123
echo     Booth Operator:    operator /  operator123
echo.
echo ===============================================================================
echo   COMMANDS:
echo     [B] Open Web App in Browser (http://localhost:3000)
echo     [D] Open Interactive API Docs (Swagger UI)
echo     [O] Setup Oracle Database (run setup_oracle_db.py)
echo     [T] Run Backend Automated Test Suite (pytest)
echo     [S] Stop all services and exit
echo     [Q] Quit this console (leaves services running in background)
echo ===============================================================================
echo.
set /p CHOICE="Enter option [B, D, O, T, S, Q]: "

if /i "%CHOICE%"=="B" (
    start http://localhost:3000
    goto MENU
)
if /i "%CHOICE%"=="D" (
    start http://127.0.0.1:8000/docs
    goto MENU
)
if /i "%CHOICE%"=="O" (
    echo.
    echo [*] Running Oracle database setup script...
    cd /d "%~dp0backend"
    .venv\Scripts\python.exe db\setup_oracle_db.py
    cd /d "%~dp0"
    echo.
    pause
    goto MENU
)
if /i "%CHOICE%"=="T" (
    echo.
    echo [*] Running automated backend test suite...
    backend\.venv\Scripts\pytest.exe backend\tests -v
    echo.
    pause
    goto MENU
)
if /i "%CHOICE%"=="S" (
    echo.
    echo [*] Shutting down SecureVote services...
    for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000"') do (
        if "%%a" neq "0" taskkill /f /pid %%a >nul 2>&1
    )
    for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3000"') do (
        if "%%a" neq "0" taskkill /f /pid %%a >nul 2>&1
    )
    taskkill /fi "WINDOWTITLE eq SecureVote - Backend Service*" /f >nul 2>&1
    taskkill /fi "WINDOWTITLE eq SecureVote - Frontend Kiosk*" /f >nul 2>&1
    echo [+] All SecureVote services terminated.
    timeout /t 2 /nobreak > nul
    exit /b 0
)
if /i "%CHOICE%"=="Q" (
    echo.
    echo Exiting controller console. Background services will remain active.
    exit /b 0
)

goto MENU
