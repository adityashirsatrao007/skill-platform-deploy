"""Tests for /api/auth endpoints."""


def test_register_user(client):
    resp = client.post("/api/auth/register", json={
        "email": "new@example.com", "password": "Pass123!",
        "full_name": "New User", "designation": "Engineer", "department": "IT",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "new@example.com"
    assert body["role"] == "learner"


def test_login_user(client):
    client.post("/api/auth/register", json={
        "email": "login@example.com", "password": "Pass123!", "full_name": "Login User",
    })
    resp = client.post("/api/auth/login", data={"username": "login@example.com", "password": "Pass123!"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_get_me(client, auth_headers):
    resp = client.get("/api/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "test@example.com"


def test_duplicate_email(client):
    payload = {"email": "dup@example.com", "password": "Pass123!", "full_name": "User"}
    client.post("/api/auth/register", json=payload)
    resp = client.post("/api/auth/register", json=payload)
    assert resp.status_code == 400


def test_invalid_credentials(client):
    client.post("/api/auth/register", json={
        "email": "wrong@example.com", "password": "Correct123!", "full_name": "User",
    })
    resp = client.post("/api/auth/login", data={"username": "wrong@example.com", "password": "Wrong1!"})
    assert resp.status_code == 401
