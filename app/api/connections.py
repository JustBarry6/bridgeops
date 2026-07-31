import json
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.crypto import encrypt
from app.core.database import get_db
from app.models.connection import Connection, ConnectionType
from app.models.user import User
from app.schemas.connection import ConnectionCreate, ConnectionOut

router = APIRouter(prefix="/connections", tags=["connections"])

REQUIRED_FIELDS = {
    ConnectionType.SFTP: {"host", "port", "username"},
    ConnectionType.AZURE_BLOB: {"connection_string"},
}


def _validate_credentials(type_: ConnectionType, credentials: dict):
    missing = REQUIRED_FIELDS[type_] - credentials.keys()
    if missing:
        raise HTTPException(422, f"Missing credential fields for {type_.value}: {missing}")
    if type_ == ConnectionType.SFTP and not (
        "password" in credentials or "private_key" in credentials
    ):
        raise HTTPException(422, "SFTP requires either 'password' or 'private_key'")


@router.post("", response_model=ConnectionOut, status_code=201)
def create_connection(
    payload: ConnectionCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: User = Depends(get_current_user),
):
    _validate_credentials(payload.type, payload.credentials)
    encrypted = encrypt(json.dumps(payload.credentials))
    connection = Connection(
        name=payload.name,
        type=payload.type,
        encrypted_credentials=encrypted,
        owner_id=current_user.id,
    )
    db.add(connection)
    db.commit()
    db.refresh(connection)
    return connection


@router.get("", response_model=list[ConnectionOut])
def list_connections(
    db: Annotated[Session, Depends(get_db)],
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Connection)
        .filter(Connection.owner_id == current_user.id)
        .order_by(Connection.created_at.desc())
        .all()
    )


@router.delete("/{connection_id}", status_code=204)
def delete_connection(
    connection_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: User = Depends(get_current_user),
):
    connection = (
        db.query(Connection)
        .filter(Connection.id == connection_id, Connection.owner_id == current_user.id)
        .first()
    )
    if not connection:
        raise HTTPException(404, "Connection not found")
    db.delete(connection)
    db.commit()