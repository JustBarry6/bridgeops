import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.connection import Connection
from app.models.transfer import Transfer
from app.models.user import User
from app.schemas.transfer import TransferCreate, TransferOut
from app.workers.tasks import execute_transfer

router = APIRouter(prefix="/transfers", tags=["transfers"])


@router.post("", response_model=TransferOut, status_code=201)
def create_transfer(
    payload: TransferCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: User = Depends(get_current_user),
):
    if payload.connection_id:
        connection = (
            db.query(Connection)
            .filter(Connection.id == payload.connection_id, Connection.owner_id == current_user.id)
            .first()
        )
        if not connection:
            raise HTTPException(404, "Connection not found")

    transfer = Transfer(
        source=payload.source,
        destination=payload.destination,
        connection_id=payload.connection_id,
        owner_id=current_user.id,
    )
    db.add(transfer)
    db.commit()
    db.refresh(transfer)

    execute_transfer.delay(str(transfer.id))

    return transfer


@router.get("", response_model=list[TransferOut])
def list_transfers(
    db: Annotated[Session, Depends(get_db)],
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Transfer)
        .filter(Transfer.owner_id == current_user.id)
        .order_by(Transfer.created_at.desc())
        .all()
    )


@router.get("/{transfer_id}", response_model=TransferOut)
def get_transfer(
    transfer_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: User = Depends(get_current_user),
):
    transfer = (
        db.query(Transfer)
        .filter(Transfer.id == transfer_id, Transfer.owner_id == current_user.id)
        .first()
    )
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")
    return transfer