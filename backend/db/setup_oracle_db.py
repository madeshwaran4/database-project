r"""
SecureVote - Oracle 21c XE Database Setup Script (Python / oracledb thin mode)

This script:
  1. Connects to Oracle XE as the SECUREVOTE_APP user (thin mode, no Oracle Client needed)
  2. Creates all required tables (skips if they already exist)
  3. Inserts seed data (admin users, candidates, election state)

Usage:
  cd backend
  .venv\Scripts\python.exe db\setup_oracle_db.py

Prerequisites:
  - Oracle 21c XE running on localhost:1521
  - SECUREVOTE_APP user created with CREATE SESSION, CREATE TABLE grants
  - Update .env with correct ORACLE_PASSWORD
"""
import os
import sys
import hashlib
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import oracledb
from app.core.config import settings


def create_tables(connection):
    """Create all SecureVote tables (safe to re-run — ignores 'name already used' errors)."""
    cursor = connection.cursor()

    tables_ddl = [
        # 1. VOTER
        """
        CREATE TABLE VOTER (
            voter_id VARCHAR2(36) PRIMARY KEY,
            name VARCHAR2(100) NOT NULL,
            id_type VARCHAR2(50) NOT NULL,
            id_last4 CHAR(4) NOT NULL,
            id_hash VARCHAR2(64) NOT NULL,
            fingerprint_template BLOB NOT NULL,
            has_voted CHAR(1) DEFAULT 'N' NOT NULL,
            enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            voted_at TIMESTAMP NULL,
            CONSTRAINT chk_voter_has_voted CHECK (has_voted IN ('Y', 'N')),
            CONSTRAINT uq_voter_id_hash UNIQUE (id_hash)
        )
        """,
        # 2. CANDIDATE
        """
        CREATE TABLE CANDIDATE (
            candidate_id VARCHAR2(36) PRIMARY KEY,
            name VARCHAR2(100) NOT NULL,
            party VARCHAR2(100) NOT NULL,
            description VARCHAR2(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
        )
        """,
        # 3. VOTE (NO link to VOTER — AGENTS.md Rule 1)
        """
        CREATE TABLE VOTE (
            vote_id VARCHAR2(36) PRIMARY KEY,
            candidate_id VARCHAR2(36) NOT NULL,
            vote_date DATE NOT NULL,
            CONSTRAINT fk_vote_candidate FOREIGN KEY (candidate_id) REFERENCES CANDIDATE(candidate_id)
        )
        """,
        # 4. VERIFICATION_LOG
        """
        CREATE TABLE VERIFICATION_LOG (
            log_id VARCHAR2(36) PRIMARY KEY,
            voter_id VARCHAR2(36) NULL,
            attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            result VARCHAR2(50) NOT NULL,
            reason VARCHAR2(255) NOT NULL,
            workstation_id VARCHAR2(50) DEFAULT 'booth-default'
        )
        """,
        # 5. ADMIN_USER
        """
        CREATE TABLE ADMIN_USER (
            admin_id VARCHAR2(36) PRIMARY KEY,
            username VARCHAR2(50) NOT NULL,
            password_hash VARCHAR2(255) NOT NULL,
            role VARCHAR2(20) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            CONSTRAINT uq_admin_username UNIQUE (username),
            CONSTRAINT chk_admin_role CHECK (role IN ('admin', 'booth-operator', 'operator'))
        )
        """,
        # 6. ELECTION_STATE
        """
        CREATE TABLE ELECTION_STATE (
            state_key VARCHAR2(50) PRIMARY KEY,
            state_value VARCHAR2(50) NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
        )
        """,
        # 7. CONSUMED_VOTE_TOKENS
        """
        CREATE TABLE CONSUMED_VOTE_TOKENS (
            token_jti VARCHAR2(36) PRIMARY KEY,
            consumed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
        )
        """,
        # 8. VERIFICATION_LOCKOUT
        """
        CREATE TABLE VERIFICATION_LOCKOUT (
            voter_id VARCHAR2(36) PRIMARY KEY,
            failed_count NUMBER(3) DEFAULT 0 NOT NULL,
            locked_until TIMESTAMP NULL,
            last_failed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
        )
        """,
    ]

    indexes_ddl = [
        "CREATE INDEX idx_voter_name ON VOTER(name)",
        "CREATE INDEX idx_voter_has_voted ON VOTER(has_voted)",
        "CREATE INDEX idx_vote_candidate ON VOTE(candidate_id)",
        "CREATE INDEX idx_vote_date ON VOTE(vote_date)",
        "CREATE INDEX idx_verif_attempted ON VERIFICATION_LOG(attempted_at)",
        "CREATE INDEX idx_verif_result ON VERIFICATION_LOG(result)",
        "CREATE INDEX idx_verif_voter ON VERIFICATION_LOG(voter_id)",
    ]

    print("[*] Creating tables...")
    for ddl in tables_ddl:
        table_name = ddl.strip().split("\n")[0].split("TABLE")[1].split("(")[0].strip()
        try:
            cursor.execute(ddl)
            print(f"    [+] Created: {table_name}")
        except oracledb.DatabaseError as e:
            error_obj = e.args[0]
            if error_obj.code == 955:  # ORA-00955: name already used
                print(f"    [=] Exists:  {table_name}")
            else:
                print(f"    [!] Error creating {table_name}: {error_obj.message}")
                raise

    print("[*] Creating indexes...")
    for ddl in indexes_ddl:
        idx_name = ddl.split("INDEX")[1].split("ON")[0].strip()
        try:
            cursor.execute(ddl)
            print(f"    [+] Created: {idx_name}")
        except oracledb.DatabaseError as e:
            error_obj = e.args[0]
            if error_obj.code == 955:  # Name already used
                print(f"    [=] Exists:  {idx_name}")
            else:
                print(f"    [!] Error: {error_obj.message}")

    connection.commit()
    cursor.close()
    print("[+] Table creation complete.")


def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 (matches app.core.security.hash_password)."""
    salt = os.urandom(16).hex()
    iterations = 100000
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    )
    return f"pbkdf2:sha256:{iterations}${salt}${derived.hex()}"


def seed_data(connection):
    """Insert seed data: election state, admin users, and candidates."""
    cursor = connection.cursor()

    # 1. Election State
    print("[*] Seeding election state...")
    cursor.execute("SELECT COUNT(*) FROM ELECTION_STATE WHERE state_key = 'polling_status'")
    count = cursor.fetchone()[0]
    if count == 0:
        cursor.execute(
            "INSERT INTO ELECTION_STATE (state_key, state_value) VALUES ('polling_status', 'closed')"
        )
        print("    [+] Inserted: polling_status = closed")
    else:
        print("    [=] Already seeded.")

    # 2. Admin Users
    print("[*] Seeding admin users...")
    cursor.execute("SELECT COUNT(*) FROM ADMIN_USER")
    count = cursor.fetchone()[0]
    if count == 0:
        admin_hash = hash_password("admin123")
        operator_hash = hash_password("operator123")

        cursor.execute(
            "INSERT INTO ADMIN_USER (admin_id, username, password_hash, role) VALUES (:1, :2, :3, :4)",
            ("admin-root-0001", "admin", admin_hash, "admin"),
        )
        cursor.execute(
            "INSERT INTO ADMIN_USER (admin_id, username, password_hash, role) VALUES (:1, :2, :3, :4)",
            ("operator-booth-0001", "operator", operator_hash, "booth-operator"),
        )
        print("    [+] Inserted: admin (admin123), operator (operator123)")
    else:
        print(f"    [=] Already seeded ({count} users exist).")

    # 3. Candidates
    print("[*] Seeding candidates...")
    cursor.execute("SELECT COUNT(*) FROM CANDIDATE")
    count = cursor.fetchone()[0]
    if count == 0:
        candidates = [
            ("cand-001", "Elena Rostova", "Democratic Alliance",
             "Focus on transparent governance, renewable infrastructure, and digital privacy."),
            ("cand-002", "Marcus Vance", "Forward Progress Coalition",
             "Platform supporting technological innovation, public healthcare expansion, and civic education."),
            ("cand-003", "Amina Chen", "Ecological Union",
             "Dedicated to sustainable city planning, clean energy transition, and ethical technology."),
        ]
        for c in candidates:
            cursor.execute(
                "INSERT INTO CANDIDATE (candidate_id, name, party, description) VALUES (:1, :2, :3, :4)", c
            )
        print(f"    [+] Inserted {len(candidates)} candidates.")
    else:
        print(f"    [=] Already seeded ({count} candidates exist).")

    connection.commit()
    cursor.close()
    print("[+] Seed data complete.")


def main():
    print("=" * 70)
    print("  SecureVote - Oracle 21c XE Database Setup (python-oracledb thin)")
    print("=" * 70)
    print()
    print(f"  Target: {settings.ORACLE_USER}@{settings.ORACLE_HOST}:{settings.ORACLE_PORT}/{settings.ORACLE_SERVICE_NAME}")
    print()

    try:
        connection = oracledb.connect(
            user=settings.ORACLE_USER,
            password=settings.ORACLE_PASSWORD,
            host=settings.ORACLE_HOST,
            port=settings.ORACLE_PORT,
            service_name=settings.ORACLE_SERVICE_NAME,
        )
        print(f"[+] Connected to Oracle in Thin mode (version: {connection.version})")
        print()
    except Exception as e:
        print(f"[!] Connection failed: {e}")
        print()
        print("    Troubleshooting:")
        print("    1. Is Oracle XE running? Check: services.msc → OracleServiceXE")
        print("    2. Is XEPDB1 open? Connect as SYS and run: ALTER PLUGGABLE DATABASE XEPDB1 OPEN;")
        print("    3. Does the user exist? Connect as SYS and run:")
        print("       CREATE USER securevote_app IDENTIFIED BY \"SecureVote2026#\"")
        print("       DEFAULT TABLESPACE USERS QUOTA UNLIMITED ON USERS;")
        print("       GRANT CREATE SESSION, CREATE TABLE TO securevote_app;")
        print()
        sys.exit(1)

    try:
        create_tables(connection)
        print()
        seed_data(connection)
    finally:
        connection.close()

    print()
    print("=" * 70)
    print("  [SUCCESS] Oracle database is ready for SecureVote!")
    print()
    print("  You can now run the application:")
    print("    Double-click run.bat  (or)  cd backend && .venv\\Scripts\\python.exe -m uvicorn app.main:app --reload")
    print("=" * 70)


if __name__ == "__main__":
    main()
