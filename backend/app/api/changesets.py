"""
ChangeSet management endpoints - Safe code modifications with apply/rollback
"""

import os
import difflib
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.changeset import ChangeSet as ChangeSetModel, Patch as PatchModel, ChangeSetStatus
from app.models.snapshot import Snapshot
from app.models.project import Project
from app.services.git_service import GitService, GitError

router = APIRouter()


# ============ Request/Response Schemas ============

class PatchCreate(BaseModel):
    file_path: str
    new_content: str


class ChangeSetCreate(BaseModel):
    snapshot_id: str
    title: str
    rationale: Optional[str] = None
    patches: List[PatchCreate]
    ai_model: Optional[str] = None
    ai_prompt: Optional[str] = None


class PatchResponse(BaseModel):
    id: str
    file_path: str
    original_content: Optional[str]
    new_content: str
    diff: str
    order: int

    class Config:
        from_attributes = True


class ChangeSetResponse(BaseModel):
    id: str
    snapshot_id: str
    title: str
    rationale: Optional[str]
    status: str
    patches: List[PatchResponse]
    created_at: datetime
    applied_at: Optional[datetime] = None
    rolled_back_at: Optional[datetime] = None
    git_commit_sha: Optional[str] = None
    git_commit_message: Optional[str] = None

    class Config:
        from_attributes = True


class CommitRequest(BaseModel):
    message: str
    author: Optional[str] = None


class ApplyResponse(BaseModel):
    status: str
    changeset_id: str
    files_modified: List[str]
    message: str


class RollbackResponse(BaseModel):
    status: str
    changeset_id: str
    files_restored: List[str]
    message: str


class CommitResponse(BaseModel):
    status: str
    changeset_id: str
    commit_sha: str
    commit_message: str


# ============ Helper Functions ============

def generate_unified_diff(original: str, new: str, file_path: str) -> str:
    """Generate a unified diff between original and new content"""
    original_lines = original.splitlines(keepends=True) if original else []
    new_lines = new.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        original_lines,
        new_lines,
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}",
        lineterm=""
    )
    return "".join(diff)


async def get_project_path(db: AsyncSession, snapshot_id: str) -> Path:
    """Get the project root path from a snapshot"""
    result = await db.execute(
        select(Snapshot)
        .options(selectinload(Snapshot.project))
        .where(Snapshot.id == snapshot_id)
    )
    snapshot = result.scalar_one_or_none()
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    
    if not snapshot.project.root_path:
        raise HTTPException(status_code=400, detail="Project has no root path")
    
    return Path(snapshot.project.root_path)


# ============ Endpoints ============

@router.post("", response_model=ChangeSetResponse)
async def create_changeset(
    request: ChangeSetCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new changeset with patches (does not apply yet)"""
    # Verify snapshot exists and get project path
    project_path = await get_project_path(db, request.snapshot_id)
    
    # Create the changeset
    changeset = ChangeSetModel(
        snapshot_id=request.snapshot_id,
        title=request.title,
        rationale=request.rationale,
        status=ChangeSetStatus.PROPOSED,
        ai_model=request.ai_model,
        ai_prompt=request.ai_prompt,
    )
    db.add(changeset)
    await db.flush()  # Get the ID
    
    # Create patches with diffs
    for idx, patch_data in enumerate(request.patches):
        file_full_path = project_path / patch_data.file_path
        
        # Read original content if file exists
        original_content = None
        if file_full_path.exists():
            try:
                original_content = file_full_path.read_text(encoding="utf-8")
            except Exception:
                original_content = ""
        
        # Generate diff
        diff = generate_unified_diff(
            original_content or "",
            patch_data.new_content,
            patch_data.file_path
        )
        
        patch = PatchModel(
            changeset_id=changeset.id,
            file_path=patch_data.file_path,
            original_content=original_content,
            new_content=patch_data.new_content,
            diff=diff,
            order=idx,
        )
        db.add(patch)
    
    await db.commit()
    await db.refresh(changeset)
    
    # Reload with patches
    result = await db.execute(
        select(ChangeSetModel)
        .options(selectinload(ChangeSetModel.patches))
        .where(ChangeSetModel.id == changeset.id)
    )
    changeset = result.scalar_one()
    
    return ChangeSetResponse(
        id=changeset.id,
        snapshot_id=changeset.snapshot_id,
        title=changeset.title,
        rationale=changeset.rationale,
        status=changeset.status.value,
        patches=[
            PatchResponse(
                id=p.id,
                file_path=p.file_path,
                original_content=p.original_content,
                new_content=p.new_content,
                diff=p.diff,
                order=p.order,
            )
            for p in sorted(changeset.patches, key=lambda x: x.order)
        ],
        created_at=changeset.created_at,
        applied_at=changeset.applied_at,
        rolled_back_at=changeset.rolled_back_at,
        git_commit_sha=changeset.git_commit_sha,
        git_commit_message=changeset.git_commit_message,
    )


@router.get("", response_model=List[ChangeSetResponse])
async def list_changesets(
    snapshot_id: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all changesets, optionally filtered"""
    query = select(ChangeSetModel).options(selectinload(ChangeSetModel.patches))
    
    if snapshot_id:
        query = query.where(ChangeSetModel.snapshot_id == snapshot_id)
    if status:
        try:
            status_enum = ChangeSetStatus(status)
            query = query.where(ChangeSetModel.status == status_enum)
        except ValueError:
            pass
    
    query = query.order_by(ChangeSetModel.created_at.desc())
    result = await db.execute(query)
    changesets = result.scalars().all()
    
    return [
        ChangeSetResponse(
            id=cs.id,
            snapshot_id=cs.snapshot_id,
            title=cs.title,
            rationale=cs.rationale,
            status=cs.status.value,
            patches=[
                PatchResponse(
                    id=p.id,
                    file_path=p.file_path,
                    original_content=p.original_content,
                    new_content=p.new_content,
                    diff=p.diff,
                    order=p.order,
                )
                for p in sorted(cs.patches, key=lambda x: x.order)
            ],
            created_at=cs.created_at,
            applied_at=cs.applied_at,
            rolled_back_at=cs.rolled_back_at,
            git_commit_sha=cs.git_commit_sha,
            git_commit_message=cs.git_commit_message,
        )
        for cs in changesets
    ]


@router.get("/{changeset_id}", response_model=ChangeSetResponse)
async def get_changeset(
    changeset_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get changeset details"""
    result = await db.execute(
        select(ChangeSetModel)
        .options(selectinload(ChangeSetModel.patches))
        .where(ChangeSetModel.id == changeset_id)
    )
    changeset = result.scalar_one_or_none()
    
    if not changeset:
        raise HTTPException(status_code=404, detail="ChangeSet not found")
    
    return ChangeSetResponse(
        id=changeset.id,
        snapshot_id=changeset.snapshot_id,
        title=changeset.title,
        rationale=changeset.rationale,
        status=changeset.status.value,
        patches=[
            PatchResponse(
                id=p.id,
                file_path=p.file_path,
                original_content=p.original_content,
                new_content=p.new_content,
                diff=p.diff,
                order=p.order,
            )
            for p in sorted(changeset.patches, key=lambda x: x.order)
        ],
        created_at=changeset.created_at,
        applied_at=changeset.applied_at,
        rolled_back_at=changeset.rolled_back_at,
        git_commit_sha=changeset.git_commit_sha,
        git_commit_message=changeset.git_commit_message,
    )


@router.post("/{changeset_id}/apply", response_model=ApplyResponse)
async def apply_changeset(
    changeset_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Apply a changeset to the repository - actually writes files"""
    result = await db.execute(
        select(ChangeSetModel)
        .options(selectinload(ChangeSetModel.patches))
        .where(ChangeSetModel.id == changeset_id)
    )
    changeset = result.scalar_one_or_none()
    
    if not changeset:
        raise HTTPException(status_code=404, detail="ChangeSet not found")
    
    if changeset.status != ChangeSetStatus.PROPOSED:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot apply changeset with status: {changeset.status.value}"
        )
    
    # Get project path
    project_path = await get_project_path(db, changeset.snapshot_id)
    
    # Verify all files still match original content (safety check)
    for patch in changeset.patches:
        file_path = project_path / patch.file_path
        if patch.original_content is not None:
            if file_path.exists():
                current_content = file_path.read_text(encoding="utf-8")
                if current_content != patch.original_content:
                    raise HTTPException(
                        status_code=409,
                        detail=f"File '{patch.file_path}' has been modified since changeset creation"
                    )
            else:
                raise HTTPException(
                    status_code=409,
                    detail=f"File '{patch.file_path}' no longer exists"
                )
    
    # Apply all patches
    files_modified = []
    try:
        for patch in sorted(changeset.patches, key=lambda x: x.order):
            file_path = project_path / patch.file_path
            
            # Create parent directories if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write new content
            file_path.write_text(patch.new_content, encoding="utf-8")
            files_modified.append(patch.file_path)
    except Exception as e:
        # Attempt to rollback on failure
        for patch in changeset.patches:
            if patch.original_content is not None:
                file_path = project_path / patch.file_path
                try:
                    file_path.write_text(patch.original_content, encoding="utf-8")
                except Exception:
                    pass
        raise HTTPException(status_code=500, detail=f"Failed to apply changes: {str(e)}")
    
    # Update changeset status
    changeset.status = ChangeSetStatus.APPLIED
    changeset.applied_at = datetime.now(timezone.utc)
    await db.commit()
    
    return ApplyResponse(
        status="applied",
        changeset_id=changeset_id,
        files_modified=files_modified,
        message=f"Successfully applied {len(files_modified)} file(s)",
    )


@router.post("/{changeset_id}/rollback", response_model=RollbackResponse)
async def rollback_changeset(
    changeset_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Rollback an applied changeset - restores original files"""
    result = await db.execute(
        select(ChangeSetModel)
        .options(selectinload(ChangeSetModel.patches))
        .where(ChangeSetModel.id == changeset_id)
    )
    changeset = result.scalar_one_or_none()
    
    if not changeset:
        raise HTTPException(status_code=404, detail="ChangeSet not found")
    
    if changeset.status != ChangeSetStatus.APPLIED:
        raise HTTPException(
            status_code=400,
            detail="Can only rollback applied changesets"
        )
    
    # Get project path
    project_path = await get_project_path(db, changeset.snapshot_id)
    
    # Restore all original files
    files_restored = []
    for patch in sorted(changeset.patches, key=lambda x: x.order, reverse=True):
        file_path = project_path / patch.file_path
        
        if patch.original_content is not None:
            # Restore original content
            file_path.write_text(patch.original_content, encoding="utf-8")
            files_restored.append(patch.file_path)
        elif file_path.exists():
            # File was created by the changeset, delete it
            file_path.unlink()
            files_restored.append(patch.file_path)
    
    # Update changeset status
    changeset.status = ChangeSetStatus.ROLLED_BACK
    changeset.rolled_back_at = datetime.now(timezone.utc)
    await db.commit()
    
    return RollbackResponse(
        status="rolled_back",
        changeset_id=changeset_id,
        files_restored=files_restored,
        message=f"Successfully rolled back {len(files_restored)} file(s)",
    )


@router.post("/{changeset_id}/commit", response_model=CommitResponse)
async def commit_changeset(
    changeset_id: str,
    request: CommitRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a git commit for an applied changeset"""
    result = await db.execute(
        select(ChangeSetModel)
        .options(selectinload(ChangeSetModel.patches))
        .where(ChangeSetModel.id == changeset_id)
    )
    changeset = result.scalar_one_or_none()
    
    if not changeset:
        raise HTTPException(status_code=404, detail="ChangeSet not found")
    
    if changeset.status != ChangeSetStatus.APPLIED:
        raise HTTPException(
            status_code=400,
            detail="Can only commit applied changesets"
        )
    
    if changeset.git_commit_sha:
        raise HTTPException(
            status_code=400,
            detail="ChangeSet already has a commit"
        )
    
    # Get project path
    project_path = await get_project_path(db, changeset.snapshot_id)
    
    # Initialize git service
    git = GitService(str(project_path))
    
    if not git.is_git_repo():
        raise HTTPException(
            status_code=400,
            detail="Project is not a git repository"
        )
    
    # Stage the modified files
    file_paths = [patch.file_path for patch in changeset.patches]
    
    try:
        git.stage_files(file_paths)
        commit = git.commit(request.message, author=request.author)
    except GitError as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # Update changeset with commit info
    changeset.git_commit_sha = commit.sha
    changeset.git_commit_message = request.message
    await db.commit()
    
    return CommitResponse(
        status="committed",
        changeset_id=changeset_id,
        commit_sha=commit.sha,
        commit_message=request.message,
    )


@router.delete("/{changeset_id}")
async def delete_changeset(
    changeset_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a changeset (only if not applied)"""
    result = await db.execute(
        select(ChangeSetModel)
        .where(ChangeSetModel.id == changeset_id)
    )
    changeset = result.scalar_one_or_none()
    
    if not changeset:
        raise HTTPException(status_code=404, detail="ChangeSet not found")
    
    if changeset.status == ChangeSetStatus.APPLIED:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete applied changesets. Rollback first."
        )
    
    await db.delete(changeset)
    await db.commit()
    
    return {"status": "deleted", "changeset_id": changeset_id}
