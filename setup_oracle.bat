@echo off
title SecureVote - Oracle 21c XE Database Setup
color 0E
cd /d "%~dp0"

echo ===============================================================================
echo         SecureVote - Oracle 21c XE Database Setup
echo ===============================================================================
echo.
echo This script will:
echo   1. Connect to Oracle 21c XE as SYS (admin)
echo   2. Create the SECUREVOTE_APP user in XEPDB1
echo   3. Create all required tables
echo   4. Insert seed data (admin users, candidates, election state)
echo.
echo ===============================================================================
echo.

:: Check if sqlplus is available
where sqlplus >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [!] sqlplus not found in PATH.
    echo     Please ensure Oracle 21c XE is installed and sqlplus is in your PATH.
    echo     Typical path: C:\app\YOURUSERNAME\product\21c\dbhomeXE\bin
    echo.
    echo     Alternatively, add Oracle to PATH:
    echo     set PATH=C:\app\YOURUSERNAME\product\21c\dbhomeXE\bin;%%PATH%%
    echo.
    pause
    exit /b 1
)

echo [*] Step 1: Creating SECUREVOTE_APP user in Oracle XEPDB1...
echo.

:: Create a temporary SQL file for user creation
(
echo SET FEEDBACK ON;
echo WHENEVER SQLERROR EXIT FAILURE ROLLBACK;
echo.
echo -- Create the application user if it doesn't exist
echo DECLARE
echo     v_count NUMBER;
echo BEGIN
echo     SELECT COUNT(*) INTO v_count FROM all_users WHERE username = 'SECUREVOTE_APP';
echo     IF v_count = 0 THEN
echo         EXECUTE IMMEDIATE 'CREATE USER securevote_app IDENTIFIED BY "SecureVote2026#" DEFAULT TABLESPACE USERS TEMPORARY TABLESPACE TEMP QUOTA UNLIMITED ON USERS';
echo         DBMS_OUTPUT.PUT_LINE('User SECUREVOTE_APP created successfully.');
echo     ELSE
echo         DBMS_OUTPUT.PUT_LINE('User SECUREVOTE_APP already exists.');
echo     END IF;
echo END;
echo /
echo.
echo -- Grant necessary privileges
echo GRANT CREATE SESSION TO securevote_app;
echo GRANT CREATE TABLE TO securevote_app;
echo GRANT CREATE SEQUENCE TO securevote_app;
echo GRANT CREATE VIEW TO securevote_app;
echo GRANT CREATE PROCEDURE TO securevote_app;
echo.
echo COMMIT;
echo EXIT SUCCESS;
) > "%TEMP%\sv_create_user.sql"

sqlplus -S "sys/oracle@localhost:1521/XEPDB1 as sysdba" @"%TEMP%\sv_create_user.sql"

if %ERRORLEVEL% neq 0 (
    echo.
    echo [!] Failed to create user. Common fixes:
    echo     - Make sure Oracle XE service is running (services.msc ^> OracleServiceXE)
    echo     - Default SYS password might differ. Try:
    echo       sqlplus "sys/YOUR_PASSWORD@localhost:1521/XEPDB1 as sysdba"
    echo.
    echo     If your SYS password is different, edit this script line:
    echo       sqlplus -S "sys/YOUR_PASSWORD@localhost:1521/XEPDB1 as sysdba"
    echo.
    del "%TEMP%\sv_create_user.sql" >nul 2>&1
    pause
    exit /b 1
)

:: Clean up temp file
del "%TEMP%\sv_create_user.sql" >nul 2>&1

echo.
echo [+] User setup complete.
echo.
echo [*] Step 2: Creating tables and indexes...
echo.

:: Run schema SQL as the app user
sqlplus -S "securevote_app/SecureVote2026#@localhost:1521/XEPDB1" @"backend\db\001_schema.sql"
if %ERRORLEVEL% neq 0 (
    echo.
    echo [!] Error running backend\db\001_schema.sql. Check the script for syntax errors.
    pause
    exit /b 1
)

echo.
echo [+] Schema created.
echo.
echo [*] Step 3: Inserting seed data...
echo.

:: Run seed SQL as the app user
sqlplus -S "securevote_app/SecureVote2026#@localhost:1521/XEPDB1" @"backend\db\002_seed.sql"
if %ERRORLEVEL% neq 0 (
    echo.
    echo [!] Error running backend\db\002_seed.sql. Check the script for syntax errors.
    pause
    exit /b 1
)

echo.
echo ===============================================================================
echo [SUCCESS] Oracle database setup complete!
echo.
echo   Database:  XEPDB1 (Pluggable Database)
echo   User:      SECUREVOTE_APP
echo   Password:  SecureVote2026#
echo   Host:      localhost:1521
echo.
echo   Tables created:
echo     - VOTER                  (enrollment records + encrypted biometrics)
echo     - CANDIDATE              (election candidates)
echo     - VOTE                   (anonymous ballots - NO link to VOTER)
echo     - VERIFICATION_LOG       (audit trail)
echo     - ADMIN_USER             (system operators/admins)
echo     - ELECTION_STATE         (polling lifecycle)
echo     - CONSUMED_VOTE_TOKENS   (replay prevention)
echo     - VERIFICATION_LOCKOUT   (failed attempt tracking)
echo.
echo   Seed accounts:
echo     admin    / admin123        (Administrator)
echo     operator / operator123     (Booth Operator)
echo ===============================================================================
echo.

pause