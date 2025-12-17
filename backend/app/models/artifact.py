from sqlalchemy import Column, Integer, String, DateTime, JSON, Enum, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from ..database import Base


class ArtifactStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class Artifact(Base):
    __tablename__ = "artifacts"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_hash = Column(String(64), nullable=False, index=True)  # SHA256
    mime_type = Column(String(127), nullable=False)
    size_bytes = Column(BigInteger, nullable=False)
    status = Column(Enum(ArtifactStatus), default=ArtifactStatus.PENDING, nullable=False)
    verification_result = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    task = relationship("Task", back_populates="artifacts")
