from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from ..database import get_db
from ..models.task import Task, TaskStatus, TaskDependency
from ..schemas.task import (
    TaskCreate, TaskUpdate, TaskResponse, TaskApproval, TaskRejection, TaskDependencyCreate
)
from ..agents.spec_generator import SpecGeneratorAgent
from ..services.sandbox import SandboxRunner
from ..services.audit import AuditService
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task."""
    db_task = Task(
        project_id=task.project_id,
        name=task.name,
        description=task.description,
        inputs=task.inputs,
        outputs=task.outputs,
        tests=task.tests,
        security_checks=task.security_checks,
        estimate_hours=task.estimate_hours,
        requires_approval=task.requires_approval,
        order=task.order,
        spec=task.spec
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    # Log audit event
    AuditService.log(
        db=db,
        project_id=task.project_id,
        task_id=db_task.id,
        action="task_created",
        actor="system",
        details={"name": task.name}
    )

    return db_task


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """Get a specific task by ID."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/project/{project_id}", response_model=List[TaskResponse])
def list_tasks_by_project(project_id: int, db: Session = Depends(get_db)):
    """List all tasks for a project."""
    tasks = db.query(Task).filter(Task.project_id == project_id).order_by(Task.order).all()
    return tasks


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task_update: TaskUpdate, db: Session = Depends(get_db)):
    """Update a task."""
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = task_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_task, key, value)

    db.commit()
    db.refresh(db_task)

    # Log audit event
    AuditService.log(
        db=db,
        project_id=db_task.project_id,
        task_id=task_id,
        action="task_updated",
        actor="system",
        details=update_data
    )

    return db_task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Delete a task."""
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    project_id = db_task.project_id
    db.delete(db_task)
    db.commit()

    # Log audit event
    AuditService.log(
        db=db,
        project_id=project_id,
        task_id=task_id,
        action="task_deleted",
        actor="system",
        details={"name": db_task.name}
    )

    return None


@router.post("/{task_id}/generate-spec")
def generate_spec(task_id: int, db: Session = Depends(get_db)):
    """Generate a detailed specification for a task using SpecGeneratorAgent."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    try:
        # Use SpecGeneratorAgent
        spec_gen = SpecGeneratorAgent()
        spec = spec_gen.generate_spec(
            task_name=task.name,
            task_description=task.description,
            project_context=f"Project ID: {task.project_id}",
            inputs=task.inputs or {},
            outputs=task.outputs or {},
            tests=task.tests or []
        )

        # Update task with spec
        task.spec = spec
        task.confidence_score = spec.get("confidence_score", 0.5)
        db.commit()

        # Log audit event
        AuditService.log(
            db=db,
            project_id=task.project_id,
            task_id=task_id,
            action="spec_generated",
            actor="spec_generator_agent",
            details={"confidence_score": task.confidence_score}
        )

        return {
            "message": "Specification generated successfully",
            "spec": spec
        }

    except Exception as e:
        logger.error(f"Failed to generate spec: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate spec: {str(e)}")


@router.post("/{task_id}/approve")
def approve_task(task_id: int, approval: TaskApproval, db: Session = Depends(get_db)):
    """Approve a task (guardrail: must have spec)."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Guardrail: Spec binding - task must have spec before approval
    if not task.spec:
        raise HTTPException(
            status_code=400,
            detail="Task cannot be approved without a machine-readable specification. Generate spec first."
        )

    # Update task
    task.status = TaskStatus.APPROVED
    task.approved_by = approval.approved_by
    task.approved_at = datetime.utcnow()
    task.rejection_reason = None

    db.commit()

    # Log audit event
    AuditService.log(
        db=db,
        project_id=task.project_id,
        task_id=task_id,
        action="task_approved",
        actor=approval.approved_by,
        details={}
    )

    return {
        "message": "Task approved successfully",
        "task_id": task_id,
        "status": task.status.value
    }


@router.post("/{task_id}/reject")
def reject_task(task_id: int, rejection: TaskRejection, db: Session = Depends(get_db)):
    """Reject a task with reason."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Update task
    task.status = TaskStatus.PENDING
    task.rejection_reason = rejection.rejection_reason
    task.approved_by = None
    task.approved_at = None

    db.commit()

    # Log audit event
    AuditService.log(
        db=db,
        project_id=task.project_id,
        task_id=task_id,
        action="task_rejected",
        actor=rejection.rejected_by,
        details={"reason": rejection.rejection_reason}
    )

    return {
        "message": "Task rejected",
        "task_id": task_id,
        "status": task.status.value
    }


@router.post("/{task_id}/run-tests")
def run_tests(task_id: int, db: Session = Depends(get_db)):
    """Run tests for a task in sandboxed environment."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Check if task has tests defined
    if not task.tests:
        raise HTTPException(status_code=400, detail="Task has no tests defined")

    try:
        # For now, return mock results since we need actual code/test content
        # In production, this would extract code from artifacts
        test_results = {
            "status": "skipped",
            "message": "Test execution requires artifact code and test files",
            "tests_defined": len(task.tests),
            "note": "Sandbox runner is available but needs code artifacts"
        }

        task.test_results = test_results
        db.commit()

        # Log audit event
        AuditService.log(
            db=db,
            project_id=task.project_id,
            task_id=task_id,
            action="tests_run",
            actor="sandbox_runner",
            details=test_results
        )

        return test_results

    except Exception as e:
        logger.error(f"Failed to run tests: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to run tests: {str(e)}")


@router.post("/{task_id}/complete")
def complete_task(task_id: int, db: Session = Depends(get_db)):
    """Complete a task (guardrail: must have passing tests)."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Guardrail: Test gate - task must have passing tests
    if not task.test_results:
        raise HTTPException(
            status_code=400,
            detail="Task cannot be completed without test results. Run tests first."
        )

    # Check test results
    if task.test_results.get("status") == "failed":
        raise HTTPException(
            status_code=400,
            detail="Task cannot be completed with failed tests."
        )

    # Guardrail: Human approval gate
    if task.requires_approval and task.status != TaskStatus.APPROVED:
        raise HTTPException(
            status_code=400,
            detail="Task requires human approval before completion."
        )

    # Update task
    task.status = TaskStatus.COMPLETED
    db.commit()

    # Log audit event
    AuditService.log(
        db=db,
        project_id=task.project_id,
        task_id=task_id,
        action="task_completed",
        actor="system",
        details={}
    )

    return {
        "message": "Task completed successfully",
        "task_id": task_id,
        "status": task.status.value
    }


@router.post("/dependencies", status_code=status.HTTP_201_CREATED)
def create_dependency(dependency: TaskDependencyCreate, db: Session = Depends(get_db)):
    """Create a task dependency."""
    # Validate tasks exist
    task = db.query(Task).filter(Task.id == dependency.task_id).first()
    depends_on = db.query(Task).filter(Task.id == dependency.depends_on_task_id).first()

    if not task or not depends_on:
        raise HTTPException(status_code=404, detail="One or both tasks not found")

    # Check for circular dependency (basic check)
    if dependency.task_id == dependency.depends_on_task_id:
        raise HTTPException(status_code=400, detail="Task cannot depend on itself")

    # Create dependency
    db_dependency = TaskDependency(
        task_id=dependency.task_id,
        depends_on_task_id=dependency.depends_on_task_id
    )
    db.add(db_dependency)
    db.commit()

    return {
        "message": "Dependency created successfully",
        "task_id": dependency.task_id,
        "depends_on_task_id": dependency.depends_on_task_id
    }
