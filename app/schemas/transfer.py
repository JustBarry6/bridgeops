import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.transfer import TransferStatus


class TransferCreate(BaseModel):
    source: str
    destination: str


class TransferOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source: str
    destination: str
    status: TransferStatus
    retry_count: int
    log: str
    created_at: datetime
    updated_at: datetime