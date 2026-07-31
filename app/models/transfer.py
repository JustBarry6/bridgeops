import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class TransferStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Transfer(Base):
    __tablename__ = "transfers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    connection_id = Column(UUID(as_uuid=True), ForeignKey("connections.id"), nullable=True)
    source = Column(Text, nullable=False)
    destination = Column(Text, nullable=False)
    status = Column(
        # values_callable force le stockage en minuscules ("queued") plutôt
        # que le nom Python de l'enum ("QUEUED"), pour rester cohérent avec l'API.
        SAEnum(TransferStatus, values_callable=lambda e: [i.value for i in e]),
        default=TransferStatus.QUEUED,
        nullable=False,
    )
    retry_count = Column(Integer, default=0)
    priority = Column(Integer, default=0)
    log = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)