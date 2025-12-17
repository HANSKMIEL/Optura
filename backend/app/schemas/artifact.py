from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from ..models.artifact import ArtifactStatus


class ArtifactResponse(BaseModel):
    model_config = {"from_attributes": True}
    
    id: int
    task_id: int
    filename: str
    original_filename: str
    file_path: str
    file_hash: str
    mime_type: str
    size_bytes: int
    status: ArtifactStatus
    verification_result: Optional[Dict[str, Any]]
    created_at: datetime


class ArtifactVerification(BaseModel):
    status: ArtifactStatus
    verification_result: Dict[str, Any] = Field(default_factory=dict)
