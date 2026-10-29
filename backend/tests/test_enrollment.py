import base64
import pytest


def test_enroll_voter_success(client, operator_token):
    # Ensure polling is closed
    fp_b64 = base64.b64encode(b"ALICE_FINGERPRINT_SAMPLE_1").decode("utf-8")
    response = client.post(
        "/api/enroll",
        headers={"Authorization": f"Bearer {operator_token}"},
        json={
            "name": "Alice Johnson",
            "id_type": "National ID",
            "id_number": "ABC-987654321",
            "fingerprint_image": fp_b64,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Alice Johnson"
    assert data["id_last4"] == "4321"
    assert data["has_voted"] == "N"
    assert "voter_id" in data


def test_enroll_duplicate_id_rejected(client, operator_token):
    fp_b64 = base64.b64encode(b"BOB_FINGERPRINT_SAMPLE_1").decode("utf-8")
    # First enrollment
    client.post(
        "/api/enroll",
        headers={"Authorization": f"Bearer {operator_token}"},
        json={
            "name": "Bob Smith",
            "id_type": "Passport",
            "id_number": "PASS-11223344",
            "fingerprint_image": fp_b64,
        },
    )

    # Second enrollment with same ID
    response = client.post(
        "/api/enroll",
        headers={"Authorization": f"Bearer {operator_token}"},
        json={
            "name": "Robert Smith",
            "id_type": "Passport",
            "id_number": "PASS-11223344",
            "fingerprint_image": base64.b64encode(b"OTHER_FINGERPRINT").decode("utf-8"),
        },
    )
    assert response.status_code == 409
    assert "already enrolled" in response.json()["detail"]


def test_enroll_duplicate_fingerprint_rejected(client, operator_token):
    same_fp = base64.b64encode(b"IDENTICAL_FINGERPRINT_FOR_FRAUD").decode("utf-8")
    # Enrolled citizen 1
    client.post(
        "/api/enroll",
        headers={"Authorization": f"Bearer {operator_token}"},
        json={
            "name": "Citizen One",
            "id_type": "Voter Card",
            "id_number": "VC-10101010",
            "fingerprint_image": same_fp,
        },
    )

    # Enrolled citizen 2 with different name/ID but SAME fingerprint
    response = client.post(
        "/api/enroll",
        headers={"Authorization": f"Bearer {operator_token}"},
        json={
            "name": "Citizen Impersonator",
            "id_type": "Driver License",
            "id_number": "DL-99999999",
            "fingerprint_image": same_fp,
        },
    )
    assert response.status_code == 409
    assert "Duplicate person" in response.json()["detail"]


def test_search_voters_returns_safe_fields_only(client, operator_token):
    response = client.get(
        "/api/voters?name=Alice",
        headers={"Authorization": f"Bearer {operator_token}"},
    )
    assert response.status_code == 200
    items = response.json()
    assert len(items) >= 1
    voter = items[0]
    assert "voter_id" in voter
    assert "name" in voter
    assert "id_last4" in voter
    assert "has_voted" in voter
    # Ensure sensitive fields are NOT present
    assert "fingerprint_template" not in voter
    assert "id_hash" not in voter
    assert "id_number" not in voter
