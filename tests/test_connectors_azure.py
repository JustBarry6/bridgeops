import uuid

import pytest

from app.connectors.azure_blob import upload_file
from app.core.config import settings


def test_upload_file_to_azurite(tmp_path):
    test_file = tmp_path / "sample.txt"
    test_file.write_text("hello from pytest")

    blob_name, file_hash = upload_file(
        source_path=str(test_file),
        container_name="pytest-container",
        transfer_id=str(uuid.uuid4()),
        connection_string=settings.azure_storage_connection_string,
    )

    assert blob_name.endswith("sample.txt")
    assert len(file_hash) == 32


def test_upload_file_missing_source_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        upload_file(
            source_path=str(tmp_path / "does-not-exist.txt"),
            container_name="pytest-container",
            transfer_id=str(uuid.uuid4()),
            connection_string=settings.azure_storage_connection_string,
        )