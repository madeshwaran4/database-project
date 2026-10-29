import base64
import pytest


def test_verification_and_vote_flow(client, operator_token, admin_token):
    # Ensure polling is closed during enrollment
    client.post("/api/admin/polling/close", headers={"Authorization": f"Bearer {admin_token}"})

    # 1. Enroll voter
    fp_raw = b"CHARLIE_FINGERPRINT_UNIQUE_01"
    fp_b64 = base64.b64encode(fp_raw).decode("utf-8")
    enroll_resp = client.post(
        "/api/enroll",
        headers={"Authorization": f"Bearer {operator_token}"},
        json={
            "name": "Charlie Brown",
            "id_type": "National ID",
            "id_number": "CHARLIE-777",
            "fingerprint_image": fp_b64,
        },
    )
    assert enroll_resp.status_code == 201
    voter_id = enroll_resp.json()["voter_id"]

    # 2. Open polling
    client.post(
        "/api/admin/polling/open",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # 3. Verify voter with matching scan
    verify_resp = client.post(
        "/api/verify",
        headers={"Authorization": f"Bearer {operator_token}"},
        json={
            "voter_id": voter_id,
            "fingerprint_scan": fp_b64,
            "workstation_id": "booth-01",
        },
    )
    assert verify_resp.status_code == 200
    v_data = verify_resp.json()
    assert v_data["allowed"] is True
    assert v_data["result"] == "SUCCESS"
    assert "vote_token" in v_data
    vote_token = v_data["vote_token"]

    # 4. Cast ballot
    vote_resp = client.post(
        "/api/vote",
        json={
            "candidate_id": "cand-001",
            "vote_token": vote_token,
        },
    )
    assert vote_resp.status_code == 201
    vote_data = vote_resp.json()
    assert vote_data["success"] is True
    assert "vote_id" in vote_data
    assert "vote_date" in vote_data  # Date only

    # 5. Token reuse blocked
    reuse_resp = client.post(
        "/api/vote",
        json={
            "candidate_id": "cand-001",
            "vote_token": vote_token,
        },
    )
    assert reuse_resp.status_code == 409

    # 6. Re-verification denied with DUPLICATE_ATTEMPT
    reverify_resp = client.post(
        "/api/verify",
        headers={"Authorization": f"Bearer {operator_token}"},
        json={
            "voter_id": voter_id,
            "fingerprint_scan": fp_b64,
        },
    )
    assert reverify_resp.status_code == 200
    assert reverify_resp.json()["allowed"] is False
    assert reverify_resp.json()["result"] == "DUPLICATE_ATTEMPT"


def test_lockout_after_n_failed_matches(client, operator_token, admin_token):
    # Ensure polling is closed during enrollment
    client.post("/api/admin/polling/close", headers={"Authorization": f"Bearer {admin_token}"})

    # Enroll voter
    fp_correct = b"DAVID_CORRECT_FINGERPRINT"
    enroll_resp = client.post(
        "/api/enroll",
        headers={"Authorization": f"Bearer {operator_token}"},
        json={
            "name": "David Miller",
            "id_type": "National ID",
            "id_number": "DAVID-5555",
            "fingerprint_image": base64.b64encode(fp_correct).decode("utf-8"),
        },
    )
    assert enroll_resp.status_code == 201
    voter_id = enroll_resp.json()["voter_id"]

    # Open polling
    client.post(
        "/api/admin/polling/open",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    bad_fp = base64.b64encode(b"WRONG_FINGERPRINT").decode("utf-8")

    # Attempt 1
    resp1 = client.post("/api/verify", headers={"Authorization": f"Bearer {operator_token}"}, json={"voter_id": voter_id, "fingerprint_scan": bad_fp})
    assert resp1.json()["result"] == "BIOMETRIC_MISMATCH"

    # Attempt 2
    resp2 = client.post("/api/verify", headers={"Authorization": f"Bearer {operator_token}"}, json={"voter_id": voter_id, "fingerprint_scan": bad_fp})
    assert resp2.json()["result"] == "BIOMETRIC_MISMATCH"

    # Attempt 3 -> Triggers lockout
    resp3 = client.post("/api/verify", headers={"Authorization": f"Bearer {operator_token}"}, json={"voter_id": voter_id, "fingerprint_scan": bad_fp})
    assert resp3.json()["result"] == "LOCKED_OUT"

    # Attempt 4 (even with correct fingerprint) is locked out!
    resp4 = client.post("/api/verify", headers={"Authorization": f"Bearer {operator_token}"}, json={"voter_id": voter_id, "fingerprint_scan": base64.b64encode(fp_correct).decode("utf-8")})
    assert resp4.json()["result"] == "LOCKED_OUT"
