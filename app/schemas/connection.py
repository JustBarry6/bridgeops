import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.connection import ConnectionType


class ConnectionCreate(BaseModel):
    name: str
    type: ConnectionType
    credentials: dict[str, str]


class ConnectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    type: ConnectionType
    created_at: datetime
    # Volontairement : jamais de champ credentials ici, même chiffré.