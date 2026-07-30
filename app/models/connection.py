import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class ConnectionType(str, enum.Enum):
    SFTP = "sftp"
    AZURE_BLOB = "azure_blob"


class Connection(Base):
    __tablename__ = "connections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    type = Column(
        SAEnum(ConnectionType, values_callable=lambda e: [i.value for i in e]),
        nullable=False,
    )
    # JSON chiffré : {host, port, username, password|private_key} pour SFTP,
    # {connection_string} pour Azure Blob.
    encrypted_credentials = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    # TODO : owner_id (FK vers User) une fois l'authentification JWT en place.