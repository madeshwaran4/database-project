"""Oracle connection pool for SecureVote (python-oracledb thin mode).

Manages an Oracle connection pool lifecycle. Provides a transactional
context manager that yields OracleSession wrappers with commit-on-success
and rollback-on-exception semantics.
"""
import logging
from contextlib import contextmanager
from typing import Generator, Any

import oracledb

from app.core.config import settings

logger = logging.getLogger("securevote.db")

_pool: oracledb.ConnectionPool | None = None


class OracleCursor:
    """Wraps an oracledb cursor to return dict-like rows with lowercase keys,
    matching the API code's expectations (e.g., row["voter_id"]).
    Also exposes rowcount for atomic update checks.
    """

    def __init__(self, raw_cursor):
        self._cursor = raw_cursor
        self._description = None

    def execute(self, sql: str, params: tuple | dict = ()):
        """Execute SQL with Oracle-style :N positional bind variables."""
        self._cursor.execute(sql, params)
        self._description = self._cursor.description

    def fetchone(self):
        row = self._cursor.fetchone()
        if row is None or self._description is None:
            return None
        columns = [col[0].lower() for col in self._description]
        return dict(zip(columns, row))

    def fetchall(self):
        rows = self._cursor.fetchall()
        if not rows or self._description is None:
            return []
        columns = [col[0].lower() for col in self._description]
        return [dict(zip(columns, row)) for row in rows]

    @property
    def rowcount(self) -> int:
        return self._cursor.rowcount

    def close(self):
        self._cursor.close()


class OracleSession:
    """Wraps an oracledb Connection to provide cursor(), commit(), rollback().
    Cursors returned are OracleCursor wrappers that give dict-style rows.
    """

    def __init__(self, connection: oracledb.Connection):
        self._conn = connection

    def cursor(self) -> OracleCursor:
        return OracleCursor(self._conn.cursor())

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()


def init_db_pool() -> None:
    """Initialize the Oracle thin-mode connection pool at app startup."""
    global _pool

    logger.info(
        "Initializing Oracle thin-mode connection pool → %s:%s/%s ...",
        settings.ORACLE_HOST,
        settings.ORACLE_PORT,
        settings.ORACLE_SERVICE_NAME,
    )
    # Return BLOBs/CLOBs directly as python bytes/str instead of LOB locators
    oracledb.defaults.fetch_lobs = False
    try:
        _pool = oracledb.create_pool(
            user=settings.ORACLE_USER,
            password=settings.ORACLE_PASSWORD,
            host=settings.ORACLE_HOST,
            port=settings.ORACLE_PORT,
            service_name=settings.ORACLE_SERVICE_NAME,
            min=settings.DB_POOL_MIN,
            max=settings.DB_POOL_MAX,
            increment=settings.DB_POOL_INCREMENT,
        )
        logger.info("Oracle connection pool initialized successfully (pool min=%d, max=%d).", settings.DB_POOL_MIN, settings.DB_POOL_MAX)
    except Exception as exc:
        logger.critical("FATAL: Cannot connect to Oracle database: %s", exc)
        raise RuntimeError(
            f"Oracle database connection failed. Ensure Oracle 21c XE is running at "
            f"{settings.ORACLE_HOST}:{settings.ORACLE_PORT}/{settings.ORACLE_SERVICE_NAME} "
            f"and credentials are correct in .env"
        ) from exc


def close_db_pool() -> None:
    """Close the Oracle connection pool at app shutdown."""
    global _pool
    if _pool is not None:
        try:
            _pool.close()
            logger.info("Oracle connection pool closed.")
        except Exception as e:
            logger.error("Error closing Oracle connection pool: %s", e)
        _pool = None


@contextmanager
def get_db_session() -> Generator[OracleSession, None, None]:
    """Context manager yielding a transactional OracleSession.
    Commits on success, rolls back on exception, always releases connection.
    """
    if _pool is None:
        raise RuntimeError("Oracle connection pool is not initialized. Call init_db_pool() first.")

    connection = _pool.acquire()
    session = OracleSession(connection)
    try:
        yield session
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        _pool.release(connection)
