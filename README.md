# SecureVote - Duplicate-Vote Prevention System

**SecureVote** is an election integrity and biometric deduplication system designed to prevent duplicate voting, credential fraud, and ballot stuffing while cryptographically guaranteeing voter privacy through zero-link anonymous ballot storage.

---

## Architecture & Monorepo Structure

```
.
├── AGENTS.md                                # Non-negotiable design & architecture rules
├── README.md                                # Root documentation & setup instructions
├── .gitignore                               # Monorepo gitignore (Python, Next.js, venvs)
├── docs/                                    # System documentation
│   ├── architecture.md                      # System architecture & Mermaid data flow diagrams
│   ├── database_er.md                       # Mermaid ER diagram & constraint definitions
│   ├── api_reference.md                     # Comprehensive REST API specifications
│   ├── setup_guide.md                       # Oracle XE 21c configuration & startup guide
│   ├── limitations.md                       # Sociotechnical & threat analysis
│   └── compliance_audit.md                  # AGENTS.md formal compliance review
├── backend/                                 # Python 3.14 FastAPI backend
│   ├── .env.example                         # Environment configuration template
│   ├── requirements.txt                     # Pinned dependencies verified on Python 3.14
│   ├── db/
│   │   ├── 001_schema.sql                   # Oracle 21c XE DDL migration script
│   │   ├── 002_seed.sql                     # Seed data (candidates, users, election state)
│   │   └── run_sql.py                       # Migration runner script (Thin mode)
│   ├── app/
│   │   ├── api/                             # API routers
│   │   │   ├── health.py                    # Health check endpoint
│   │   │   ├── auth.py                      # Operator & admin authentication
│   │   │   ├── enrollment.py                # Citizen registration & duplicate detection
│   │   │   ├── voting.py                    # Biometric verification & atomic ballot casting
│   │   │   └── admin.py                     # Candidate CRUD, polling toggle, results, audit logs
│   │   ├── core/                            # Settings, crypto, middleware & sanitization
│   │   ├── db/                              # Oracle pool & testing SQLite engine
│   │   ├── fingerprint/                     # Biometric provider abstraction & AES cipher
│   │   ├── schemas/                         # Pydantic v2 schemas
│   │   └── main.py                          # FastAPI entrypoint
│   └── tests/                               # 21 automated tests covering all flows
└── frontend/                                # Next.js 16 (App Router), TypeScript, Tailwind CSS
    ├── app/
    │   ├── page.tsx                         # System landing hub
    │   ├── login/page.tsx                   # Staff authentication with quick-fill demo buttons
    │   ├── enroll/page.tsx                  # Citizen biometric registration portal
    │   ├── booth/page.tsx                   # Kiosk-friendly 5-step voting booth flow
    │   └── admin/page.tsx                   # Admin control, candidate slate, results, and audit logs
    ├── components/
    │   ├── Navbar.tsx                       # Navigation bar with live polling status indicator
    │   └── FingerprintScanner.tsx           # Biometric sensor simulator with scanline animation
    └── lib/
        └── api.ts                           # Typed API client for backend communication
```

---

## Non-Negotiable Design Rules ([AGENTS.md](AGENTS.md))

1. **Absolute Voter / Vote Separation**: The `VOTE` table has **NO** relationship (no foreign keys, no voter IDs, and no timestamp finer than a date) to the `VOTER` table.
2. **Random UUIDs**: Every `vote_id` is a cryptographically generated UUIDv4, never a database sequence or incremental ID.
3. **Atomic Eligibility Flip & Vote Insertion**: Flipping `has_voted` from `'N'` to `'Y'` and inserting the ballot must execute in the exact same transaction:
   ```sql
   UPDATE VOTER SET has_voted = 'Y', voted_at = SYSDATE WHERE voter_id = :voter_id AND has_voted = 'N';
   ```
   If updated rows = 0, the transaction immediately rolls back to eliminate race conditions.
4. **Hashed Identification**: Never store full government/national ID numbers—store only the last 4 digits plus a high-entropy salted hash (`id_hash = SHA256(salt + id)`).
5. **Application-Level Biometric Encryption**: Fingerprint minutiae templates are encrypted at the application layer (AES-256) prior to database persistence.
6. **Comprehensive Verification Logging**: Every voter verification attempt (permitted, denied, duplicate, or biometric mismatch) is recorded in `VERIFICATION_LOG`.
7. **Environment-Driven Configuration**: No secrets in source code; all credentials and encryption keys are injected via environment variables (`.env.example`).

---

## Quickstart Guide

### 1. Backend Setup (FastAPI & Python 3.14)

```powershell
cd backend
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
```

To run all 21 automated test suites:
```powershell
pytest tests/ -v
```

To launch the backend API:
```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
* **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

### 2. Frontend Setup (Next.js & Tailwind CSS)

```powershell
cd frontend
npm install
npm run dev
```
* **Application Portal**: [http://localhost:3000](http://localhost:3000)
* **Voting Booth Kiosk**: [http://localhost:3000/booth](http://localhost:3000/booth)
* **Voter Enrollment**: [http://localhost:3000/enroll](http://localhost:3000/enroll)
* **Admin Dashboard**: [http://localhost:3000/admin](http://localhost:3000/admin)
* **Staff Login**: [http://localhost:3000/login](http://localhost:3000/login)

---

## Demo Credentials

| Role | Username | Password | Default Capabilities |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin` | `admin123` | Polling lifecycle control, candidate CRUD, certified results |
| **Booth Operator** | `operator` | `operator123` | Voter check-in, biometric 1:1 verification, enrollment |

---

## System Documentation

* [System Architecture & Data Flows](docs/architecture.md)
* [Entity-Relationship Diagram & Database Decoupling](docs/database_er.md)
* [Comprehensive API Reference](docs/api_reference.md)
* [Oracle 21c XE Setup & Migration Manual](docs/setup_guide.md)
* [Threat Analysis & System Limitations](docs/limitations.md)
* [AGENTS.md Compliance Audit](docs/compliance_audit.md)
