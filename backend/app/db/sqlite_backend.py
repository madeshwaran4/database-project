import os
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Generator
from app.core.config import settings
from app.core.security import hash_password

_local = threading.local()
_db_initialized = False
_init_lock = threading.Lock()


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0].lower()] = row[idx]
    return d


def init_sqlite_db() -> sqlite3.Connection:
    global _db_initialized
    with _init_lock:
        db_path = settings.SQLITE_DB_PATH
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = dict_factory
        conn.execute("PRAGMA foreign_keys = ON;")

        # Create tables if not exist
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS VOTER (
            voter_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            id_type TEXT NOT NULL,
            id_last4 TEXT NOT NULL,
            id_hash TEXT NOT NULL UNIQUE,
            fingerprint_template BLOB NOT NULL,
            has_voted TEXT DEFAULT 'N' NOT NULL CHECK (has_voted IN ('Y', 'N')),
            enrolled_at TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL,
            voted_at TEXT NULL
        );

        CREATE TABLE IF NOT EXISTS CANDIDATE (
            candidate_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            party TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL
        );

        CREATE TABLE IF NOT EXISTS VOTE (
            vote_id TEXT PRIMARY KEY,
            candidate_id TEXT NOT NULL,
            vote_date TEXT NOT NULL,
            FOREIGN KEY (candidate_id) REFERENCES CANDIDATE(candidate_id)
        );

        CREATE TABLE IF NOT EXISTS VERIFICATION_LOG (
            log_id TEXT PRIMARY KEY,
            voter_id TEXT NULL,
            attempted_at TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL,
            result TEXT NOT NULL,
            reason TEXT NOT NULL,
            workstation_id TEXT DEFAULT 'booth-default'
        );

        CREATE TABLE IF NOT EXISTS ADMIN_USER (
            admin_id TEXT PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('admin', 'booth-operator', 'operator')),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL
        );

        CREATE TABLE IF NOT EXISTS ELECTION_STATE (
            state_key TEXT PRIMARY KEY,
            state_value TEXT NOT NULL,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL
        );

        CREATE TABLE IF NOT EXISTS CONSUMED_VOTE_TOKENS (
            token_jti TEXT PRIMARY KEY,
            consumed_at TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL
        );

        CREATE TABLE IF NOT EXISTS VERIFICATION_LOCKOUT (
            voter_id TEXT PRIMARY KEY,
            failed_count INTEGER DEFAULT 0 NOT NULL,
            locked_until TEXT NULL,
            last_failed_at TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL
        );
        """)

        # Insert initial election state and seed users if empty
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM ELECTION_STATE WHERE state_key = 'polling_status'")
        row = cursor.fetchone()
        if row["count"] == 0:
            cursor.execute("INSERT INTO ELECTION_STATE (state_key, state_value) VALUES ('polling_status', 'closed')")

        cursor.execute("SELECT COUNT(*) as count FROM ADMIN_USER")
        row = cursor.fetchone()
        if row["count"] == 0:
            admin_hash = hash_password("admin123")
            operator_hash = hash_password("operator123")
            cursor.execute("""
            INSERT INTO ADMIN_USER (admin_id, username, password_hash, role)
            VALUES 
            ('admin-001', 'admin', ?, 'admin'),
            ('op-001', 'operator', ?, 'booth-operator');
            """, (admin_hash, operator_hash))

        cursor.execute("SELECT COUNT(*) as count FROM CANDIDATE")
        row = cursor.fetchone()
        if row["count"] == 0:
            cursor.execute("""
            INSERT INTO CANDIDATE (candidate_id, name, party, description)
            VALUES 
            ('cand-001', 'Elena Rostova', 'Democratic Alliance', 'Focus on transparent governance, renewable infrastructure, and digital privacy.'),
            ('cand-002', 'Marcus Vance', 'Forward Progress Coalition', 'Platform supporting technological innovation, public healthcare expansion, and civic education.'),
            ('cand-003', 'Amina Chen', 'Ecological Union', 'Dedicated to sustainable city planning, clean energy transition, and ethical technology.');
            """)

        conn.commit()
        _db_initialized = True
        return conn


@contextmanager
def get_sqlite_session() -> Generator[sqlite3.Connection, None, None]:
    if not hasattr(_local, "connection") or _local.connection is None:
        db_path = settings.SQLITE_DB_PATH
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        _local.connection = sqlite3.connect(db_path, timeout=30.0, check_same_thread=False)
        _local.connection.row_factory = dict_factory
        _local.connection.execute("PRAGMA foreign_keys = ON;")

    conn = _local.connection
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
