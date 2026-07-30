import os
import uuid

import pytest

from app.connectors.sftp import upload_file

SFTP_TEST_HOST = os.environ.get("SFTP_TEST_HOST", "sftp-test")
SFTP_TEST_PORT = int(os.environ.get("SFTP_TEST_PORT", "22"))


def test_upload_file_via_sftp(tmp_path):
    test_file = tmp_path / f"{uuid.uuid4()}.txt"
    test_file.write_text("hello from pytest via sftp")

    upload_file(
        source_path=str(test_file),
        remote_path=f"upload/{test_file.name}",
        host=SFTP_TEST_HOST,
        port=SFTP_TEST_PORT,
        username="testuser",
        password="testpass",
    )


def test_upload_file_wrong_credentials_raises(tmp_path):
    test_file = tmp_path / "sample.txt"
    test_file.write_text("hello")

    with pytest.raises(Exception):
        upload_file(
            source_path=str(test_file),
            remote_path="upload/sample.txt",
            host=SFTP_TEST_HOST,
            port=SFTP_TEST_PORT,
            username="testuser",
            password="wrong-password",
        )