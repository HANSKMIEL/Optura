from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import os
import hashlib
import aiofiles
from datetime import datetime
from ..database import get_db
from ..models.task import Task
from ..models.artifact import Artifact, ArtifactStatus
from ..schemas.artifact import ArtifactResponse, ArtifactVerification
from ..services.file_validator import FileValidator
from ..services.audit import AuditService
from ..agents.verifier import VerifierAgent
from ..config import settings
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


# Ensure upload directory exists
os.makedirs(settings.upload_dir, exist_ok=True)


@router.post("/task/{task_id}", response_model=ArtifactResponse, status_code=status.HTTP_201_CREATED)
async def upload_artifact(task_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload an artifact for a task."""
    # Verify task exists
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Read file content
    content = await file.read()
    size_bytes = len(content)

    # Validate file
    is_valid, error = FileValidator.validate_file(file.filename, size_bytes)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)

    # Validate content
    is_valid, error = FileValidator.validate_content(content, file.content_type or "application/octet-stream")
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)

    # Calculate SHA256 hash
    file_hash = hashlib.sha256(content).hexdigest()

    # Sanitize filename
    original_filename = file.filename
    safe_filename = FileValidator.sanitize_filename(file.filename)

    # Create unique filename with hash prefix
    filename = f"{file_hash[:8]}_{safe_filename}"
    file_path = os.path.join(settings.upload_dir, filename)

    # Save file
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save file")

    # Create artifact record
    artifact = Artifact(
        task_id=task_id,
        filename=filename,
        original_filename=original_filename,
        file_path=file_path,
        file_hash=file_hash,
        mime_type=file.content_type or "application/octet-stream",
        size_bytes=size_bytes,
        status=ArtifactStatus.PENDING
    )
    db.add(artifact)
    db.commit()
    db.refresh(artifact)

    # Log audit event
    AuditService.log(
        db=db,
        project_id=task.project_id,
        task_id=task_id,
        action="artifact_uploaded",
        actor="system",
        details={
            "filename": original_filename,
            "size_bytes": size_bytes,
            "file_hash": file_hash
        }
    )

    return artifact


@router.get("/{artifact_id}", response_model=ArtifactResponse)
def get_artifact(artifact_id: int, db: Session = Depends(get_db)):
    """Get artifact details."""
    artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact


@router.get("/task/{task_id}", response_model=List[ArtifactResponse])
def list_task_artifacts(task_id: int, db: Session = Depends(get_db)):
    """List all artifacts for a task."""
    artifacts = db.query(Artifact).filter(Artifact.task_id == task_id).all()
    return artifacts


@router.post("/{artifact_id}/verify")
def verify_artifact(artifact_id: int, db: Session = Depends(get_db)):
    """Verify an artifact using the VerifierAgent."""
    artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    task = db.query(Task).filter(Task.id == artifact.task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    try:
        # Read file content
        with open(artifact.file_path, 'rb') as f:
            content = f.read()

        # Try to decode as text
        try:
            file_content = content.decode('utf-8')
        except UnicodeDecodeError:
            file_content = f"[Binary file, {len(content)} bytes]"

        # Use VerifierAgent
        verifier = VerifierAgent()
        verification = verifier.verify_artifact(
            filename=artifact.original_filename,
            mime_type=artifact.mime_type,
            size_bytes=artifact.size_bytes,
            file_content=file_content,
            task_name=task.name,
            task_description=task.description,
            expected_outputs=task.outputs or {}
        )

        # Update artifact
        artifact.verification_result = verification

        # Set status based on verification
        if verification.get("status") == "pass":
            artifact.status = ArtifactStatus.VERIFIED
        elif verification.get("status") == "fail":
            artifact.status = ArtifactStatus.REJECTED
        else:
            artifact.status = ArtifactStatus.PENDING

        db.commit()

        # Log audit event
        AuditService.log(
            db=db,
            project_id=task.project_id,
            task_id=task.id,
            action="artifact_verified",
            actor="verifier_agent",
            details={
                "artifact_id": artifact_id,
                "status": artifact.status.value,
                "overall_score": verification.get("overall_score")
            }
        )

        return {
            "message": "Artifact verified",
            "artifact_id": artifact_id,
            "status": artifact.status.value,
            "verification": verification
        }

    except Exception as e:
        logger.error(f"Failed to verify artifact: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to verify artifact: {str(e)}")


@router.delete("/{artifact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_artifact(artifact_id: int, db: Session = Depends(get_db)):
    """Delete an artifact."""
    artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    # Delete file
    try:
        if os.path.exists(artifact.file_path):
            os.remove(artifact.file_path)
    except Exception as e:
        logger.error(f"Failed to delete file: {e}")

    # Delete record
    db.delete(artifact)
    db.commit()

    return None
