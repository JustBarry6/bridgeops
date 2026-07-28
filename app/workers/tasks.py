import uuid

from app.connectors.azure_blob import upload_file
from app.core.database import SessionLocal
from app.models.transfer import Transfer, TransferStatus
from app.workers.celery_app import celery_app


@celery_app.task(name="execute_transfer")
def execute_transfer(transfer_id: str):
    db = SessionLocal()
    try:
        transfer = db.query(Transfer).filter(Transfer.id == uuid.UUID(transfer_id)).first()
        if not transfer:
            return

        transfer.status = TransferStatus.RUNNING
        transfer.log += "Transfer started\n"
        db.commit()

        try:
            blob_name, file_hash = upload_file(
                source_path=transfer.source,
                container_name=transfer.destination,
                transfer_id=str(transfer.id),
            )
            transfer.status = TransferStatus.COMPLETED
            transfer.log += f"Uploaded to blob '{blob_name}' (md5={file_hash})\n"
        except Exception as exc:
            transfer.status = TransferStatus.FAILED
            transfer.log += f"Transfer failed: {exc}\n"

        db.commit()
    finally:
        db.close()