from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
from ..models.task import TaskStatus


class TaskCreate(BaseModel):
    project_id: int
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    tests: List[Dict[str, Any]] = Field(default_factory=list)
    security_checks: List[Dict[str, Any]] = Field(default_factory=list)
    estimate_hours: Optional[float] = None
    requires_approval: bool = False
    order: int = 0
    spec: Optional[Dict[str, Any]] = None


class TaskUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    inputs: Optional[Dict[str, Any]] = None
    outputs: Optional[Dict[str, Any]] = None
    tests: Optional[List[Dict[str, Any]]] = None
    security_checks: Optional[List[Dict[str, Any]]] = None
    estimate_hours: Optional[float] = None
    status: Optional[TaskStatus] = None
    confidence_score: Optional[float] = None
    requires_approval: Optional[bool] = None
    order: Optional[int] = None
    spec: Optional[Dict[str, Any]] = None
    test_results: Optional[Dict[str, Any]] = None


class TaskResponse(BaseModel):
    model_config = {"from_attributes": True}
    
    id: int
    project_id: int
    name: str
    description: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    tests: List[Dict[str, Any]]
    security_checks: List[Dict[str, Any]]
    estimate_hours: Optional[float]
    status: TaskStatus
    confidence_score: Optional[float]
    requires_approval: bool
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    rejection_reason: Optional[str]
    order: int
    spec: Optional[Dict[str, Any]]
    test_results: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class TaskApproval(BaseModel):
    approved_by: str = Field(..., min_length=1)


class TaskRejection(BaseModel):
    rejected_by: str = Field(..., min_length=1)
    rejection_reason: str = Field(..., min_length=1)


class TaskDependencyCreate(BaseModel):
    task_id: int
    depends_on_task_id: int
