import time
import uuid

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

        time.sleep(3)  # simulation — sera remplacé par un vrai connecteur

        transfer.status = TransferStatus.COMPLETED
        transfer.log += "Transfer completed\n"
        db.commit()
    finally:
        db.close()