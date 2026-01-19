"""
Project management endpoints
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid

router = APIRouter()


class ProjectCreate(BaseModel):
    name: str
    path: Optional[str] = None  # Local path
    

class Project(BaseModel):
    id: str
    name: str
    path: Optional[str]
    created_at: datetime
    snapshot_count: int = 0


class ProjectImportResponse(BaseModel):
    id: str
    name: str
    status: str
    message: str


# In-memory store for MVP (replace with DB)
_projects: dict[str, Project] = {}


@router.get("", response_model=List[Project])
async def list_projects():
    """List all projects"""
    return list(_projects.values())


@router.post("/import", response_model=ProjectImportResponse)
async def import_project(data: ProjectCreate):
    """Import a new project from local path or upload"""
    project_id = str(uuid.uuid4())
    
    project = Project(
        id=project_id,
        name=data.name,
        path=data.path,
        created_at=datetime.utcnow(),
        snapshot_count=0,
    )
    _projects[project_id] = project
    
    return ProjectImportResponse(
        id=project_id,
        name=data.name,
        status="pending",
        message="Project imported. Run snapshot to index.",
    )


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: str):
    """Get project details"""
    if project_id not in _projects:
        raise HTTPException(status_code=404, detail="Project not found")
    return _projects[project_id]


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    """Delete a project"""
    if project_id not in _projects:
        raise HTTPException(status_code=404, detail="Project not found")
    del _projects[project_id]
    return {"status": "deleted"}


@router.post("/{project_id}/snapshots")
async def create_snapshot(project_id: str):
    """Kick off indexing for a new snapshot"""
    if project_id not in _projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    snapshot_id = str(uuid.uuid4())
    
    # TODO: Queue indexing job
    return {
        "snapshot_id": snapshot_id,
        "status": "indexing",
        "message": "Snapshot indexing started",
    }
