import base64
import concurrent.futures
from app.core.security import create_vote_token
from app.db.pool import get_db_session


def test_concurrent_simultaneous_voting_race_condition(client, admin_token, operator_token):
    """Concurrency test: Two simultaneous vote requests for the same voter must result in EXACTLY ONE vote.
    Constraint (AGENTS.md Rule 3): Atomic rowcount check aborts the race condition.
    """
    # 1. Close polling first to permit enrollment
    client.post(
        "/api/admin/polling/close",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # 2. Enroll voter
    fp_raw = b"CONCURRENT_VOTER_SAMPLE"
    fp_b64 = base64.b64encode(fp_raw).decode("utf-8")
    enroll_resp = client.post(
        "/api/enroll",
        headers={"Authorization": f"Bearer {operator_token}"},
        json={
            "name": "Evelyn Concurrent",
            "id_type": "National ID",
            "id_number": "CONCUR-12345",
            "fingerprint_image": fp_b64,
        },
    )
    assert enroll_resp.status_code == 201
    voter_id = enroll_resp.json()["voter_id"]

    # 3. Open polling for voting
    client.post(
        "/api/admin/polling/open",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # 4. Create two valid vote tokens for the same voter (simulating simultaneous booth submissions or duplicated network packet)
    token_1 = create_vote_token(voter_id)
    token_2 = create_vote_token(voter_id)

    # 5. Dispatch simultaneous POST /api/vote requests in parallel threads
    results = []

    def cast(token):
        return client.post(
            "/api/vote",
            json={"candidate_id": "cand-001", "vote_token": token},
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(cast, token_1), executor.submit(cast, token_2)]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())

    status_codes = [r.status_code for r in results]

    # Exactly one request must succeed (201 Created) and one must be rejected (409 Conflict)
    assert 201 in status_codes, f"Expected a 201 success in {status_codes}"
    assert 409 in status_codes, f"Expected a 409 duplicate rejection in {status_codes}"

    # Verify database state has has_voted = 'Y' for voter
    with get_db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT has_voted FROM VOTER WHERE voter_id = :1", (voter_id,))
        voter = cursor.fetchone()
        assert (voter["has_voted"] if isinstance(voter, dict) else voter[0]) == "Y"
