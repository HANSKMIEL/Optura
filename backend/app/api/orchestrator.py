from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.project import Project
from ..services.orchestrator import OrchestratorService
from ..services.audit import AuditService
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/project/{project_id}/critical-path")
def get_critical_path(project_id: int, db: Session = Depends(get_db)):
    """Calculate and return the critical path for a project."""
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        result = OrchestratorService.calculate_critical_path(project_id, db)
        return result
    except Exception as e:
        logger.error(f"Failed to calculate critical path: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate critical path: {str(e)}")


@router.get("/project/{project_id}/dependency-graph")
def get_dependency_graph(project_id: int, db: Session = Depends(get_db)):
    """Get the dependency graph for visualization."""
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        result = OrchestratorService.get_dependency_graph(project_id, db)
        return result
    except Exception as e:
        logger.error(f"Failed to get dependency graph: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get dependency graph: {str(e)}")


@router.post("/project/{project_id}/reprioritize")
def reprioritize_tasks(project_id: int, db: Session = Depends(get_db)):
    """Reprioritize tasks based on status and dependencies."""
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        result = OrchestratorService.reprioritize(project_id, db)

        # Log audit event if changes were made
        if result["changes"]:
            AuditService.log(
                db=db,
                project_id=project_id,
                action="tasks_reprioritized",
                actor="orchestrator_service",
                details={
                    "change_count": len(result["changes"]),
                    "changes": result["changes"]
                }
            )

        return result
    except Exception as e:
        logger.error(f"Failed to reprioritize tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reprioritize tasks: {str(e)}")


@router.get("/project/{project_id}/next-actions")
def get_next_actions(project_id: int, db: Session = Depends(get_db)):
    """Get suggested next actions for a project."""
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        result = OrchestratorService.suggest_next_actions(project_id, db)
        return result
    except Exception as e:
        logger.error(f"Failed to get next actions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get next actions: {str(e)}")


@router.get("/project/{project_id}/status-summary")
def get_status_summary(project_id: int, db: Session = Depends(get_db)):
    """Get a status summary for a project."""
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        from ..models.task import Task, TaskStatus

        # Get task counts by status
        tasks = db.query(Task).filter(Task.project_id == project_id).all()

        status_counts = {}
        for status in TaskStatus:
            status_counts[status.value] = 0

        total_estimate = 0
        completed_estimate = 0

        for task in tasks:
            status_counts[task.status.value] += 1
            if task.estimate_hours:
                total_estimate += task.estimate_hours
                if task.status == TaskStatus.COMPLETED:
                    completed_estimate += task.estimate_hours

        # Calculate progress
        progress = (completed_estimate / total_estimate * 100) if total_estimate > 0 else 0

        # Get critical path
        critical_path = OrchestratorService.calculate_critical_path(project_id, db)

        # Get next actions
        next_actions = OrchestratorService.suggest_next_actions(project_id, db)

        return {
            "project_id": project_id,
            "project_name": project.name,
            "status": project.status.value,
            "risk_level": project.risk_level.value,
            "task_counts": status_counts,
            "total_tasks": len(tasks),
            "total_estimate_hours": total_estimate,
            "completed_estimate_hours": completed_estimate,
            "progress_percent": round(progress, 2),
            "critical_path_hours": critical_path.get("total_hours", 0),
            "next_actions": next_actions.get("actionable", [])[:3],
            "needs_approval": next_actions.get("needs_approval", [])
        }

    except Exception as e:
        logger.error(f"Failed to get status summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status summary: {str(e)}")
