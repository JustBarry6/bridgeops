import hashlib
from pathlib import Path

from azure.storage.blob import BlobServiceClient, ContentSettings

from app.core.config import settings


def _get_blob_service_client(connection_string: str) -> BlobServiceClient:
    return BlobServiceClient.from_connection_string(connection_string)


def _ensure_container(client: BlobServiceClient, container_name: str):
    container_client = client.get_container_client(container_name)
    if not container_client.exists():
        container_client.create_container()
    return container_client


def _file_md5(path: Path) -> str:
    hash_md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def upload_file(
    source_path: str,
    container_name: str,
    transfer_id: str,
    connection_string: str | None = None,
) -> tuple[str, str]:
    path = Path(source_path)
    if not path.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}")

    connection_string = connection_string or settings.azure_storage_connection_string
    blob_name = f"{transfer_id}_{path.name}"

    client = _get_blob_service_client(connection_string)
    container_client = _ensure_container(client, container_name)
    blob_client = container_client.get_blob_client(blob_name)
    local_hash = _file_md5(path)

    with open(path, "rb") as data:
        blob_client.upload_blob(
            data, overwrite=True, validate_content=True,
            content_settings=ContentSettings(content_type="application/octet-stream"),
        )

    return blob_name, local_hash