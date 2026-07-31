def test_register_creates_user(client):
    response = client.post("/auth/register", json={"email": "new@example.com", "password": "secret123"})
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new@example.com"
    assert "password" not in body
    assert "hashed_password" not in body


def test_register_duplicate_email_rejected(client):
    client.post("/auth/register", json={"email": "dup@example.com", "password": "secret123"})
    response = client.post("/auth/register", json={"email": "dup@example.com", "password": "other456"})
    assert response.status_code == 400


def test_login_success_returns_token(client):
    client.post("/auth/register", json={"email": "login@example.com", "password": "secret123"})
    response = client.post(
        "/auth/login", data={"username": "login@example.com", "password": "secret123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_wrong_password_rejected(client):
    client.post("/auth/register", json={"email": "wrong@example.com", "password": "secret123"})
    response = client.post(
        "/auth/login", data={"username": "wrong@example.com", "password": "not-the-password"},
    )
    assert response.status_code == 401


def test_transfers_endpoint_requires_authentication(client):
    response = client.get("/transfers")
    assert response.status_code == 401