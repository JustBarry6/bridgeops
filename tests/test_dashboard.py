def test_dashboard_redirects_when_not_authenticated(client):
    response = client.get("/dashboard", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard/login"


def test_login_page_renders(client):
    response = client.get("/dashboard/login")
    assert response.status_code == 200
    assert "BridgeOps" in response.text


def test_dashboard_renders_when_authenticated(client):
    client.post("/auth/register", json={"email": "dash@example.com", "password": "secret123"})
    login_response = client.post(
        "/dashboard/login",
        data={"email": "dash@example.com", "password": "secret123"},
        follow_redirects=False,
    )
    assert login_response.status_code == 303

    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "dash@example.com" in response.text