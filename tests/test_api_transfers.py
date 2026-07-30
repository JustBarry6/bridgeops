import uuid
from unittest.mock import patch


@patch("app.api.transfers.execute_transfer")
def test_create_transfer_dispatches_task(mock_execute_transfer, client):
    response = client.post(
        "/transfers",
        json={"source": "sample-files/test.txt", "destination": "transfers"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "queued"
    mock_execute_transfer.delay.assert_called_once_with(body["id"])


def test_get_transfer_not_found_returns_404(client):
    response = client.get(f"/transfers/{uuid.uuid4()}")
    assert response.status_code == 404


@patch("app.api.transfers.execute_transfer")
def test_list_transfers_returns_created_transfer(mock_execute_transfer, client):
    create_response = client.post(
        "/transfers",
        json={"source": "sample-files/test.txt", "destination": "transfers"},
    )
    transfer_id = create_response.json()["id"]

    response = client.get("/transfers")
    assert transfer_id in [t["id"] for t in response.json()]