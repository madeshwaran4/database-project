import pytest


def test_candidate_crud_and_polling_blocks(client, admin_token):
    # Ensure closed
    client.post("/api/admin/polling/close", headers={"Authorization": f"Bearer {admin_token}"})

    # Add candidate succeeds when closed
    cand_resp = client.post(
        "/api/candidates",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Dr. Sarah Connor",
            "party": "Independent Tech Reform",
            "description": "Cybersecurity advocate.",
        },
    )
    assert cand_resp.status_code == 201
    cand_id = cand_resp.json()["candidate_id"]

    # Open polling
    open_resp = client.post("/api/admin/polling/open", headers={"Authorization": f"Bearer {admin_token}"})
    assert open_resp.status_code == 200
    assert open_resp.json()["is_open"] is True

    # Candidate creation BLOCKED once polling is open (Phase 6 rule)
    blocked_create = client.post(
        "/api/candidates",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Late Candidate", "party": "Late Party"},
    )
    assert blocked_create.status_code == 400

    # Candidate deletion BLOCKED once polling is open
    blocked_delete = client.delete(
        f"/api/candidates/{cand_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert blocked_delete.status_code == 400


def test_results_locked_until_polling_closes(client, admin_token):
    # Open polling
    client.post("/api/admin/polling/open", headers={"Authorization": f"Bearer {admin_token}"})

    # Accessing results while polling is OPEN must return 403 Forbidden!
    results_open = client.get("/api/results")
    assert results_open.status_code == 403
    assert "sealed and locked" in results_open.json()["detail"]

    # Close polling
    client.post("/api/admin/polling/close", headers={"Authorization": f"Bearer {admin_token}"})

    # Accessing results after close succeeds
    results_closed = client.get("/api/results")
    assert results_closed.status_code == 200
    data = results_closed.json()
    assert "total_votes" in data
    assert "results" in data
    assert data["polling_status"] == "closed"


def test_logs_and_stats(client, admin_token, operator_token):
    # Stats endpoint
    stats_resp = client.get("/api/stats", headers={"Authorization": f"Bearer {operator_token}"})
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert "enrolled_voters" in stats
    assert "votes_cast" in stats
    assert "denied_attempts" in stats

    # Logs endpoint
    logs_resp = client.get("/api/logs", headers={"Authorization": f"Bearer {operator_token}"})
    assert logs_resp.status_code == 200
    logs = logs_resp.json()
    assert "items" in logs
    assert "total" in logs
