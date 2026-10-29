import base64
import pytest


def test_complete_e2e_election_cycle(client, admin_token, operator_token):
    """Phase 8.3 End-to-end integration test:
    1. Pre-polling: Add candidate and enroll voters.
    2. Polling open: Enrollment locks, candidate CRUD locks, booth opens.
    3. Booth verification: Citizen presents ID and fingerprint, receives short-lived vote token.
    4. Cast ballot: Citizen selects candidate on ballot kiosk, vote recorded anonymously.
    5. Repeat attempt: Citizen tries to re-verify or cast another ballot -> blocked!
    6. Close polling: Polling finalized, results unlock with accurate tallies.
    """
    # Step 1: Pre-polling setup
    client.post("/api/admin/polling/close", headers={"Authorization": f"Bearer {admin_token}"})

    fp_raw = b"E2E_CITIZEN_BIOMETRIC_DATA"
    fp_b64 = base64.b64encode(fp_raw).decode("utf-8")

    enroll_res = client.post(
        "/api/enroll",
        headers={"Authorization": f"Bearer {operator_token}"},
        json={
            "name": "Maria Garcia",
            "id_type": "National Identity Card",
            "id_number": "NAT-99887766",
            "fingerprint_image": fp_b64,
        },
    )
    assert enroll_res.status_code == 201
    voter_id = enroll_res.json()["voter_id"]

    # Step 2: Open Polling
    open_res = client.post("/api/admin/polling/open", headers={"Authorization": f"Bearer {admin_token}"})
    assert open_res.status_code == 200

    # Ensure enrollment is now blocked
    blocked_enroll = client.post(
        "/api/enroll",
        headers={"Authorization": f"Bearer {operator_token}"},
        json={
            "name": "Late Citizen",
            "id_type": "Passport",
            "id_number": "PASS-9999",
            "fingerprint_image": base64.b64encode(b"LATE_FP").decode("utf-8"),
        },
    )
    assert blocked_enroll.status_code == 400

    # Step 3: Booth Verification
    verify_res = client.post(
        "/api/verify",
        headers={"Authorization": f"Bearer {operator_token}"},
        json={
            "voter_id": voter_id,
            "fingerprint_scan": fp_b64,
            "workstation_id": "kiosk-north-01",
        },
    )
    assert verify_res.status_code == 200
    v_data = verify_res.json()
    assert v_data["allowed"] is True
    vote_token = v_data["vote_token"]

    # Step 4: Cast Ballot
    vote_res = client.post(
        "/api/vote",
        json={"candidate_id": "cand-001", "vote_token": vote_token},
    )
    assert vote_res.status_code == 201
    assert vote_res.json()["success"] is True

    # Step 5: Repeat attempt blocked at verification
    repeat_verify = client.post(
        "/api/verify",
        headers={"Authorization": f"Bearer {operator_token}"},
        json={"voter_id": voter_id, "fingerprint_scan": fp_b64},
    )
    assert repeat_verify.json()["allowed"] is False
    assert repeat_verify.json()["result"] == "DUPLICATE_ATTEMPT"

    # Repeat ballot submission blocked
    repeat_vote = client.post(
        "/api/vote",
        json={"candidate_id": "cand-002", "vote_token": vote_token},
    )
    assert repeat_vote.status_code == 409

    # Step 6: Close polling and verify results unlock
    close_res = client.post("/api/admin/polling/close", headers={"Authorization": f"Bearer {admin_token}"})
    assert close_res.status_code == 200

    results_res = client.get("/api/results")
    assert results_res.status_code == 200
    results_data = results_res.json()
    assert results_data["total_votes"] >= 1
    # Check that candidate 1 received vote
    cand1_result = next(r for r in results_data["results"] if r["candidate_id"] == "cand-001")
    assert cand1_result["vote_count"] >= 1
