import uuid

from celery.utils.log import get_task_logger

from app.connectors.azure_blob import upload_file
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.transfer import Transfer, TransferStatus
from app.workers.celery_app import celery_app

logger = get_task_logger(__name__)

MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 5


class SimulatedFailure(Exception):
    """Levée uniquement si SIMULATE_FAILURE=true, pour rendre le retry visible en démo."""


@celery_app.task(name="execute_transfer", bind=True, max_retries=MAX_RETRIES)
def execute_transfer(self, transfer_id: str):
    db = SessionLocal()
    # self.request.retries vaut 0 au premier passage, puis Celery l'incrémente
    # automatiquement à chaque appel de self.retry().
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

        blob_name, file_hash = upload_file(
            source_path=transfer.source,
            container_name=transfer.destination,
            transfer_id=str(transfer.id),
        )
        transfer.status = TransferStatus.COMPLETED
        transfer.log += (
            f"Attempt {attempt} succeeded: uploaded to blob "
            f"'{blob_name}' (md5={file_hash})\n"
        )
        db.commit()

    except Exception as exc:
        if attempt <= MAX_RETRIES:
            countdown = RETRY_BACKOFF_SECONDS * (2 ** (attempt - 1))  # backoff exponentiel : 5s, 10s, 20s
            transfer.log += f"Attempt {attempt} failed: {exc}. Retrying in {countdown}s...\n"
            transfer.status = TransferStatus.QUEUED
            db.commit()
            raise self.retry(exc=exc, countdown=countdown)
        else:
            transfer.log += (
                f"Attempt {attempt} failed: {exc}. "
                f"No more retries ({MAX_RETRIES} max) — marking as failed.\n"
            )
            transfer.status = TransferStatus.FAILED
            db.commit()

    finally:
        db.close()