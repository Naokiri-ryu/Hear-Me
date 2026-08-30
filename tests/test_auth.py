def test_register_login_me(client):
    resp = client.post(
        "/auth/register",
        json={"email": "new@example.com", "password": "password123", "display_name": "New"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["email"] == "new@example.com"

    resp = client.post(
        "/auth/login",
        json={"email": "new@example.com", "password": "password123"},
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]

    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["id"] == body["id"]


def test_register_duplicate_email(client):
    payload = {"email": "dup@example.com", "password": "password123"}
    assert client.post("/auth/register", json=payload).status_code == 201
    assert client.post("/auth/register", json=payload).status_code == 409


def test_login_wrong_password(client):
    client.post(
        "/auth/register",
        json={"email": "wrong@example.com", "password": "password123"},
    )
    resp = client.post(
        "/auth/login",
        json={"email": "wrong@example.com", "password": "nope-nope"},
    )
    assert resp.status_code == 401


def test_me_requires_token(client):
    assert client.get("/auth/me").status_code == 401


def test_register_rejects_short_password(client):
    resp = client.post(
        "/auth/register",
        json={"email": "short@example.com", "password": "1234567"},
    )
    assert resp.status_code == 422