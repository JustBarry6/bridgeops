import json
import uuid

from celery.utils.log import get_task_logger

from app.connectors.azure_blob import upload_file as upload_to_azure_blob
from app.connectors.sftp import upload_file as upload_to_sftp
from app.core.config import settings
from app.core.crypto import decrypt
from app.core.database import SessionLocal
from app.models.connection import Connection, ConnectionType
from app.models.transfer import Transfer, TransferStatus
from app.workers.celery_app import celery_app

logger = get_task_logger(__name__)

MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 5


class SimulatedFailure(Exception):
    pass


def _execute_via_connection(transfer: Transfer, connection: Connection) -> str:
    credentials = json.loads(decrypt(connection.encrypted_credentials))

    if connection.type == ConnectionType.SFTP:
        upload_to_sftp(
            source_path=transfer.source,
            remote_path=transfer.destination,
            host=credentials["host"],
            port=int(credentials["port"]),
            username=credentials["username"],
            password=credentials.get("password"),
            private_key=credentials.get("private_key"),
        )
        return f"Uploaded via SFTP to '{transfer.destination}' using connection '{connection.name}'"

    blob_name, file_hash = upload_to_azure_blob(
        source_path=transfer.source,
        container_name=transfer.destination,
        transfer_id=str(transfer.id),
        connection_string=credentials["connection_string"],
    )
    return f"Uploaded to blob '{blob_name}' (md5={file_hash}) using connection '{connection.name}'"


@celery_app.task(name="execute_transfer", bind=True, max_retries=MAX_RETRIES)
def execute_transfer(self, transfer_id: str):
    db = SessionLocal()
    attempt = self.request.retries + 1

    try:
        transfer = db.query(Transfer).filter(Transfer.id == uuid.UUID(transfer_id)).first()
        if not transfer:
            return

        transfer.retry_count = self.request.retries
        transfer.status = TransferStatus.RUNNING
        transfer.log += f"Attempt {attempt} started\n"
        db.commit()

        if settings.simulate_failure and attempt == 1:
            raise SimulatedFailure("Simulated network timeout")

        if transfer.connection_id:
            connection = db.query(Connection).filter(Connection.id == transfer.connection_id).first()
            if not connection:
                raise ValueError(f"Connection {transfer.connection_id} not found")
            result_message = _execute_via_connection(transfer, connection)
        else:
            # Compatibilité : transferts sans connexion -> Azure Blob par défaut (dev/tests).
            blob_name, file_hash = upload_to_azure_blob(
                source_path=transfer.source,
                container_name=transfer.destination,
                transfer_id=str(transfer.id),
            )
            result_message = f"Uploaded to blob '{blob_name}' (md5={file_hash}) [default connection]"

        transfer.status = TransferStatus.COMPLETED
        transfer.log += f"Attempt {attempt} succeeded: {result_message}\n"
        db.commit()

    except Exception as exc:
        if attempt <= MAX_RETRIES:
            countdown = RETRY_BACKOFF_SECONDS * (2 ** (attempt - 1))
            transfer.log += f"Attempt {attempt} failed: {exc}. Retrying in {countdown}s...\n"
            transfer.status = TransferStatus.QUEUED
            db.commit()
            raise self.retry(exc=exc, countdown=countdown)
        else:
            transfer.log += f"Attempt {attempt} failed: {exc}. No more retries — marking as failed.\n"
            transfer.status = TransferStatus.FAILED
            db.commit()
    finally:
        db.close()