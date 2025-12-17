from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from ..models.project import ProjectStatus, RiskLevel


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    goal: str = Field(..., min_length=1)
    acceptance_criteria: List[str] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    environment: Optional[str] = None
    deadline: Optional[datetime] = None
    created_by: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    goal: Optional[str] = Field(None, min_length=1)
    acceptance_criteria: Optional[List[str]] = None
    risk_level: Optional[RiskLevel] = None
    status: Optional[ProjectStatus] = None
    environment: Optional[str] = None
    deadline: Optional[datetime] = None


class ProjectResponse(BaseModel):
    model_config = {"from_attributes": True}
    
    id: int
    name: str
    description: str
    goal: str
    acceptance_criteria: List[str]
    risk_level: RiskLevel
    status: ProjectStatus
    environment: Optional[str]
    deadline: Optional[datetime]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseModel):
    projects: List[ProjectResponse]
    total: int
