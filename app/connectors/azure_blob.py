import hashlib
from pathlib import Path

from azure.storage.blob import BlobServiceClient, ContentSettings

from app.core.config import settings


def _get_blob_service_client() -> BlobServiceClient:
    return BlobServiceClient.from_connection_string(
        settings.azure_storage_connection_string
    )


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


def upload_file(source_path: str, container_name: str, transfer_id: str) -> tuple[str, str]:
    """
    Upload un fichier local vers Azure Blob Storage (Azurite en dev).
    Le nom du blob est déterministe (basé sur transfer_id) : un retry du
    même transfert écrase le même blob au lieu d'en créer un nouveau.
    """
    path = Path(source_path)
    if not path.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}")

    blob_name = f"{transfer_id}_{path.name}"

    client = _get_blob_service_client()
    container_client = _ensure_container(client, container_name)
    blob_client = container_client.get_blob_client(blob_name)

    local_hash = _file_md5(path)

    with open(path, "rb") as data:
        blob_client.upload_blob(
            data,
            overwrite=True,
            # Le SDK calcule un MD5 pendant le transfert et Azure (ou Azurite)
            # rejette l'upload en cas de corruption détectée.
            validate_content=True,
            content_settings=ContentSettings(content_type="application/octet-stream"),
        )

    return blob_name, local_hash