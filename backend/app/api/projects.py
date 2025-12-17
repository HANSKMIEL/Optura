from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models.project import Project, ProjectStatus
from ..models.task import Task, TaskDependency
from ..models.audit import AuditLog
from ..schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse
from ..schemas.task import TaskCreate
from ..agents.planner import PlannerAgent
from ..services.audit import AuditService
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    """Create a new project."""
    db_project = Project(
        name=project.name,
        description=project.description,
        goal=project.goal,
        acceptance_criteria=project.acceptance_criteria,
        risk_level=project.risk_level,
        environment=project.environment,
        deadline=project.deadline,
        created_by=project.created_by or "system"
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    # Log audit event
    AuditService.log(
        db=db,
        project_id=db_project.id,
        action="project_created",
        actor=project.created_by or "system",
        details={"name": project.name, "goal": project.goal}
    )

    return db_project


@router.get("/", response_model=ProjectListResponse)
def list_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all projects."""
    projects = db.query(Project).offset(skip).limit(limit).all()
    total = db.query(Project).count()
    return {"projects": projects, "total": total}


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    """Get a specific project by ID."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: int, project_update: ProjectUpdate, db: Session = Depends(get_db)):
    """Update a project."""
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = project_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_project, key, value)

    db.commit()
    db.refresh(db_project)

    # Log audit event
    AuditService.log(
        db=db,
        project_id=project_id,
        action="project_updated",
        actor="system",
        details=update_data
    )

    return db_project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    """Delete a project."""
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")

    db.delete(db_project)
    db.commit()
    return None


@router.post("/{project_id}/generate-plan")
def generate_plan(project_id: int, db: Session = Depends(get_db)):
    """Generate a task plan for a project using the PlannerAgent."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        # Use PlannerAgent to generate plan
        planner = PlannerAgent()
        plan = planner.generate_plan(
            project_name=project.name,
            goal=project.goal,
            description=project.description,
            acceptance_criteria=project.acceptance_criteria or [],
            environment=project.environment or ""
        )

        # Create tasks from plan
        created_tasks = []
        task_map = {}  # Map plan index to task ID

        for idx, task_data in enumerate(plan.get("tasks", [])):
            task = Task(
                project_id=project_id,
                name=task_data["name"],
                description=task_data["description"],
                inputs=task_data.get("inputs", {}),
                outputs=task_data.get("outputs", {}),
                tests=task_data.get("tests", []),
                security_checks=task_data.get("security_checks", []),
                estimate_hours=task_data.get("estimate_hours"),
                order=task_data.get("order", idx),
                requires_approval=task_data.get("requires_approval", False),
                confidence_score=task_data.get("confidence_score")
            )
            db.add(task)
            db.flush()  # Get task ID
            task_map[idx] = task.id
            created_tasks.append(task)

        # Create dependencies
        for idx, task_data in enumerate(plan.get("tasks", [])):
            for dep_idx in task_data.get("dependencies", []):
                if dep_idx in task_map:
                    dependency = TaskDependency(
                        task_id=task_map[idx],
                        depends_on_task_id=task_map[dep_idx]
                    )
                    db.add(dependency)

        # Update project risk level and status
        if "risk_level" in plan:
            project.risk_level = plan["risk_level"]
        project.status = ProjectStatus.PLANNING

        db.commit()

        # Log audit event
        AuditService.log(
            db=db,
            project_id=project_id,
            action="plan_generated",
            actor="planner_agent",
            details={
                "task_count": len(created_tasks),
                "estimated_total_hours": plan.get("estimated_total_hours", 0)
            }
        )

        return {
            "message": "Plan generated successfully",
            "task_count": len(created_tasks),
            "estimated_total_hours": plan.get("estimated_total_hours", 0),
            "risk_level": plan.get("risk_level", "medium")
        }

    except Exception as e:
        logger.error(f"Failed to generate plan: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate plan: {str(e)}")


@router.get("/{project_id}/audit-log")
def get_audit_log(project_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get audit log for a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    logs = db.query(AuditLog).filter(
        AuditLog.project_id == project_id
    ).order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "project_id": project_id,
        "logs": [
            {
                "id": log.id,
                "action": log.action,
                "actor": log.actor,
                "task_id": log.task_id,
                "details": log.details,
                "created_at": log.created_at
            }
            for log in logs
        ]
    }
