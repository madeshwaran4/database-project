import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

TEST_DB_PATH = "backend/db/test_securevote.db"

# Configure environment for tests before importing app
os.environ["ENVIRONMENT"] = "testing"
os.environ["DEBUG"] = "True"
os.environ["FINGERPRINT_PROVIDER"] = "mock"

from app.main import app
from app.core.config import settings
from app.db.pool import init_db_pool, close_db_pool


@pytest.fixture(scope="session", autouse=True)
def setup_test_suite_db():
    """Initialize Oracle DB pool for testing session."""
    init_db_pool()
    yield
    close_db_pool()


@pytest.fixture(autouse=True)
def reset_db_state():
    """Reset dynamic tables and election state between test runs."""
    from app.db.pool import get_db_session
    try:
        with get_db_session() as db:
            cursor = db.cursor()
            cursor.execute("DELETE FROM VOTE")
            cursor.execute("DELETE FROM CONSUMED_VOTE_TOKENS")
            cursor.execute("DELETE FROM VERIFICATION_LOCKOUT")
            cursor.execute("DELETE FROM VERIFICATION_LOG")
            cursor.execute("DELETE FROM VOTER")
            cursor.execute(
                "UPDATE ELECTION_STATE SET state_value = 'closed', updated_at = CURRENT_TIMESTAMP WHERE state_key = 'polling_status'"
            )
    except Exception:
        pass
    yield


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def admin_token(client):
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture
def operator_token(client):
    response = client.post(
        "/api/auth/login",
        json={"username": "operator", "password": "operator123"},
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]
