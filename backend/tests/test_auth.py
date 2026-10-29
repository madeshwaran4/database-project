def test_login_success_admin(client):
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "admin"
    assert data["username"] == "admin"


def test_login_success_operator(client):
    response = client.post(
        "/api/auth/login",
        json={"username": "operator", "password": "operator123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "booth-operator"


def test_login_invalid_password(client):
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "wrongpassword"},
    )
    assert response.status_code == 401


def test_role_check_admin_endpoint_forbidden_for_operator(client, operator_token):
    # Only admin can open polling
    response = client.post(
        "/api/admin/polling/open",
        headers={"Authorization": f"Bearer {operator_token}"},
    )
    assert response.status_code == 403
