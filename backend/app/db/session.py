from typing import Generator, Any
from fastapi import Depends
from app.db.pool import get_db_session


def get_db() -> Generator[Any, None, None]:
    """FastAPI Dependency for transactional database access.
    Yields an active database session/connection. Automatically commits on successful
    request completion or rolls back if an exception occurs.
    """
    with get_db_session() as session:
        yield session
