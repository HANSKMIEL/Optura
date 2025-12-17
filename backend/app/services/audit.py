import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from ..models.audit import AuditLog

logger = logging.getLogger(__name__)


class AuditService:
    """Service for logging audit events."""

    @staticmethod
    def log(
        db: Session,
        project_id: int,
        action: str,
        actor: str,
        details: Dict[str, Any] = None,
        task_id: Optional[int] = None
    ) -> AuditLog:
        """
        Log an audit event.

        Args:
            db: Database session
            project_id: ID of the project
            action: Action performed (e.g., "project_created", "task_approved")
            actor: User or system that performed the action
            details: Additional details about the action
            task_id: Optional task ID if action is task-specific

        Returns:
            Created AuditLog instance
        """
        try:
            audit_log = AuditLog(
                project_id=project_id,
                task_id=task_id,
                action=action,
                actor=actor,
                details=details or {}
            )
            db.add(audit_log)
            db.commit()
            db.refresh(audit_log)

            logger.info(
                f"Audit log created: project={project_id}, action={action}, "
                f"actor={actor}, task={task_id}"
            )

            return audit_log

        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            db.rollback()
            raise
