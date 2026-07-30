import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.transfer import Transfer
from app.schemas.transfer import TransferCreate, TransferOut
from app.workers.tasks import execute_transfer

router = APIRouter(prefix="/transfers", tags=["transfers"])


@router.post("", response_model=TransferOut, status_code=201)
def create_transfer(payload: TransferCreate, db: Session = Depends(get_db)):
    transfer = Transfer(
        source=payload.source,
        destination=payload.destination,
        connection_id=payload.connection_id,
    )
    db.add(transfer)
    db.commit()
    db.refresh(transfer)

    execute_transfer.delay(str(transfer.id))

    return transfer


@router.get("", response_model=list[TransferOut])
def list_transfers(db: Session = Depends(get_db)):
    return db.query(Transfer).order_by(Transfer.created_at.desc()).all()


@router.get("/{transfer_id}", response_model=TransferOut)
def get_transfer(transfer_id: uuid.UUID, db: Session = Depends(get_db)):
    transfer = db.query(Transfer).filter(Transfer.id == transfer_id).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")
    return transfer