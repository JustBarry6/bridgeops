def test_create_connection_encrypts_credentials(authenticated_client, db_session):
    response = authenticated_client.post(
        "/connections",
        json={
            "name": "test-sftp",
            "type": "sftp",
            "credentials": {
                "host": "sftp-test", "port": "22",
                "username": "testuser", "password": "testpass",
            },
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert "credentials" not in body
    assert "encrypted_credentials" not in body

    from app.models.connection import Connection
    connection = db_session.query(Connection).filter(Connection.id == body["id"]).first()
    assert "testpass" not in connection.encrypted_credentials


def test_create_connection_missing_fields_returns_422(authenticated_client):
    response = authenticated_client.post(
        "/connections",
        json={"name": "bad-sftp", "type": "sftp", "credentials": {"host": "x"}},
    )
    assert response.status_code == 422


def test_list_connections_never_exposes_credentials(authenticated_client):
    authenticated_client.post(
        "/connections",
        json={
            "name": "test-blob",
            "type": "azure_blob",
            "credentials": {"connection_string": "UseDevelopmentStorage=true"},
        },
    )
    response = authenticated_client.get("/connections")
    assert response.status_code == 200
    for connection in response.json():
        assert "credentials" not in connection
        assert "encrypted_credentials" not in connection