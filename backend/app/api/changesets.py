"""
ChangeSet management endpoints
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

router = APIRouter()


class ChangeSetStatus(str, Enum):
    proposed = "proposed"
    applied = "applied"
    rolled_back = "rolled_back"


class Patch(BaseModel):
    file_path: str
    original_content: str
    new_content: str
    diff: str


class ChangeSet(BaseModel):
    id: str
    snapshot_id: str
    title: str
    rationale: str
    status: ChangeSetStatus
    patches: List[Patch]
    created_at: datetime
    applied_at: Optional[datetime] = None


class CommitRequest(BaseModel):
    message: str


# In-memory store
_changesets: dict[str, ChangeSet] = {}


@router.get("", response_model=List[ChangeSet])
async def list_changesets(snapshot_id: Optional[str] = None):
    """List all changesets, optionally filtered by snapshot"""
    results = list(_changesets.values())
    if snapshot_id:
        results = [cs for cs in results if cs.snapshot_id == snapshot_id]
    return results


@router.get("/{changeset_id}", response_model=ChangeSet)
async def get_changeset(changeset_id: str):
    """Get changeset details"""
    if changeset_id not in _changesets:
        raise HTTPException(status_code=404, detail="ChangeSet not found")
    return _changesets[changeset_id]


@router.post("/{changeset_id}/apply")
async def apply_changeset(changeset_id: str):
    """Apply a changeset to the repository"""
    if changeset_id not in _changesets:
        raise HTTPException(status_code=404, detail="ChangeSet not found")
    
    cs = _changesets[changeset_id]
    if cs.status != ChangeSetStatus.proposed:
        raise HTTPException(status_code=400, detail=f"Cannot apply changeset with status: {cs.status}")
    
    # TODO: Actually apply patches
    cs.status = ChangeSetStatus.applied
    cs.applied_at = datetime.utcnow()
    
    return {"status": "applied", "changeset_id": changeset_id}


@router.post("/{changeset_id}/rollback")
async def rollback_changeset(changeset_id: str):
    """Rollback an applied changeset"""
    if changeset_id not in _changesets:
        raise HTTPException(status_code=404, detail="ChangeSet not found")
    
    cs = _changesets[changeset_id]
    if cs.status != ChangeSetStatus.applied:
        raise HTTPException(status_code=400, detail="Can only rollback applied changesets")
    
    # TODO: Actually rollback patches
    cs.status = ChangeSetStatus.rolled_back
    
    return {"status": "rolled_back", "changeset_id": changeset_id}


@router.post("/{changeset_id}/commit")
async def commit_changeset(changeset_id: str, request: CommitRequest):
    """Create a git commit for an applied changeset"""
    if changeset_id not in _changesets:
        raise HTTPException(status_code=404, detail="ChangeSet not found")
    
    cs = _changesets[changeset_id]
    if cs.status != ChangeSetStatus.applied:
        raise HTTPException(status_code=400, detail="Can only commit applied changesets")
    
    # TODO: Create git commit
    return {
        "status": "committed",
        "changeset_id": changeset_id,
        "commit_message": request.message,
        "commit_sha": "abc123...",  # Would be real SHA
    }
