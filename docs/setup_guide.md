# SecureVote Setup & Deployment Guide

This guide covers setting up Oracle 21c XE (or local SQLite fallback), running database migrations, configuring environment variables, and starting the FastAPI backend and Next.js frontend.

---

## 1. Prerequisites

* **Python**: Python 3.14 (with `py -3.14` or `python` on PATH)
* **Node.js**: Node.js v20+ with `npm`
* **Oracle Database**: Oracle Database 21c XE (Express Edition) or Oracle Free 23c.
  *(Note: SecureVote uses `python-oracledb` in Thin mode, requiring **no** Oracle Instant Client or C-libraries).*

---

## 2. Oracle 21c XE Configuration

### Step A: Verify Oracle Service and Listener
Ensure your Oracle XE Windows service and TNS listener are active:
```powershell
# In Windows PowerShell (Administrator):
Get-Service *oracle*
Start-Service OracleServiceXE
Start-Service OracleOraDB21Home1TNSListener
```

### Step B: Create Application User and Tablespace
Connect via `sqlplus` as `sysdba`:
```sql
sqlplus sys/<your_sys_password>@localhost:1521/XEPDB1 as sysdba
```
Execute user creation script:
```sql
CREATE USER securevote_app IDENTIFIED BY "YourSecurePassword2026#"
  DEFAULT TABLESPACE users
  TEMPORARY TABLESPACE temp
  QUOTA UNLIMITED ON users;

GRANT CONNECT, RESOURCE, CREATE VIEW, CREATE SEQUENCE TO securevote_app;
COMMIT;
EXIT;
```

---

## 3. Backend Environment Configuration

1. In the `backend/` directory, copy `.env.example` to `.env`:
   ```bash
   cp backend/.env.example backend/.env
   ```

2. Configure environment keys:
   ```ini
   # Oracle Database Configuration (Thin Mode)
   DB_BACKEND=oracle
   ORACLE_USER=securevote_app
   ORACLE_PASSWORD=YourSecurePassword2026#
   ORACLE_HOST=localhost
   ORACLE_PORT=1521
   ORACLE_SERVICE_NAME=XEPDB1

   # Connection Pool Settings
   DB_POOL_MIN=2
   DB_POOL_MAX=10
   DB_POOL_INCREMENT=1

   # Security & Cryptography
   SECRET_KEY=generate_with_openssl_rand_hex_32
   BIOMETRIC_ENCRYPTION_KEY=s2l8yX0T_M0Vv5X2i3H_yYjX4Y8kQ7qZ8k1a2b3c4d4=
   ID_HASH_SALT=securevote_high_entropy_salt_change_in_production

   # Biometric Provider (mock, dataset, or usb)
   FINGERPRINT_PROVIDER=mock
   FINGERPRINT_MATCH_THRESHOLD=40.0
   ```

---

## 4. Run Database Schema & Seed Scripts

Run the Python migration runner:
```powershell
.\backend\.venv\Scripts\python.exe backend/db/run_sql.py
```
This executes:
1. `backend/db/001_schema.sql`: Creates `VOTER`, `CANDIDATE`, `VOTE`, `VERIFICATION_LOG`, `ADMIN_USER`, and `ELECTION_STATE`.
2. `backend/db/002_seed.sql`: Seeds initial candidates and default staff accounts:
   - **Administrator**: `admin` / `admin123`
   - **Booth Operator**: `operator` / `operator123`

---

## 5. Start Backend Server

```powershell
cd backend
.\.venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
* **API Health Check**: [http://localhost:8000/health](http://localhost:8000/health)
* **Interactive OpenAPI Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 6. Start Next.js Frontend

```powershell
cd frontend
npm install
npm run dev
```
* **Web Application URL**: [http://localhost:3000](http://localhost:3000)

---

## 7. Run Test Suite

To run all automated unit, integration, concurrency, and security tests:
```powershell
.\backend\.venv\Scripts\pytest.exe backend/tests -v
```
All 21 test suites will run and pass using the isolated testing database.
