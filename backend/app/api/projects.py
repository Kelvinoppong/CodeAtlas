"""
Project management endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.project import Project
from app.models.snapshot import Snapshot, SnapshotStatus
from app.indexer.engine import IndexingEngine
from app.services.git_service import GitService

router = APIRouter()


class ProjectCreate(BaseModel):
    name: str
    path: Optional[str] = None
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    root_path: Optional[str]
    created_at: datetime
    snapshot_count: int = 0

    class Config:
        from_attributes = True


class ProjectImportResponse(BaseModel):
    id: str
    name: str
    status: str
    message: str
    is_git_repo: bool = False
    git_branch: Optional[str] = None


class SnapshotResponse(BaseModel):
    snapshot_id: str
    status: str
    message: str
    git_branch: Optional[str] = None
    git_commit: Optional[str] = None


class BranchSnapshotRequest(BaseModel):
    branch: str


@router.get("", response_model=List[ProjectResponse])
async def list_projects(db: AsyncSession = Depends(get_db)):
    """List all projects"""
    result = await db.execute(select(Project))
    projects = result.scalars().all()

    responses = []
    for project in projects:
        # Count snapshots
        snap_result = await db.execute(
            select(Snapshot).where(Snapshot.project_id == project.id)
        )
        snapshot_count = len(snap_result.scalars().all())

        responses.append(ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            root_path=project.root_path,
            created_at=project.created_at,
            snapshot_count=snapshot_count,
        ))

    return responses


@router.post("/import", response_model=ProjectImportResponse)
async def import_project(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
):
    """Import a new project from local path"""
    # Validate path exists
    is_git_repo = False
    git_branch = None
    
    if data.path:
        path = Path(data.path).resolve()
        if not path.exists():
            raise HTTPException(status_code=400, detail=f"Path does not exist: {data.path}")
        if not path.is_dir():
            raise HTTPException(status_code=400, detail=f"Path is not a directory: {data.path}")
        
        # Check if it's a git repo
        git = GitService(str(path))
        is_git_repo = git.is_git_repo()
        if is_git_repo:
            git_branch = git.get_current_branch()

    project = Project(
        name=data.name,
        description=data.description,
        root_path=str(Path(data.path).resolve()) if data.path else None,
        default_branch=git_branch,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    return ProjectImportResponse(
        id=project.id,
        name=project.name,
        status="created",
        message="Project imported. Run POST /projects/{id}/snapshots to start indexing.",
        is_git_repo=is_git_repo,
        git_branch=git_branch,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """Get project details"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Count snapshots
    snap_result = await db.execute(
        select(Snapshot).where(Snapshot.project_id == project.id)
    )
    snapshot_count = len(snap_result.scalars().all())

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        root_path=project.root_path,
        created_at=project.created_at,
        snapshot_count=snapshot_count,
    )


@router.delete("/{project_id}")
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a project and all its snapshots"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    await db.delete(project)
    await db.commit()

    return {"status": "deleted", "id": project_id}


async def run_indexing(project_id: str, db: AsyncSession):
    """Background task to run indexing"""
    engine = IndexingEngine(db)
    try:
        await engine.index_project(project_id)
    except Exception as e:
        print(f"Indexing failed for project {project_id}: {e}")


@router.post("/{project_id}/snapshots", response_model=SnapshotResponse)
async def create_snapshot(
    project_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Start indexing a new snapshot"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.root_path:
        raise HTTPException(status_code=400, detail="Project has no root path configured")

    # Create pending snapshot
    snapshot = Snapshot(
        project_id=project_id,
        status=SnapshotStatus.PENDING,
    )
    db.add(snapshot)
    await db.commit()
    await db.refresh(snapshot)

    # Start indexing in background
    # Note: In production, use a proper task queue like Celery
    # background_tasks.add_task(run_indexing, project_id, db)

    return SnapshotResponse(
        snapshot_id=snapshot.id,
        status="pending",
        message="Snapshot created. Indexing will start shortly.",
    )


@router.post("/{project_id}/snapshots/sync", response_model=SnapshotResponse)
async def create_snapshot_sync(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Start indexing synchronously (for development)"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.root_path:
        raise HTTPException(status_code=400, detail="Project has no root path configured")

    # Get git info
    git_branch = None
    git_commit = None
    git = GitService(project.root_path)
    if git.is_git_repo():
        git_branch = git.get_current_branch()
        git_commit = git.get_current_commit()

    # Run indexing synchronously
    engine = IndexingEngine(db)
    snapshot = await engine.index_project(project_id, git_branch=git_branch, git_commit=git_commit)

    return SnapshotResponse(
        snapshot_id=snapshot.id,
        status=snapshot.status.value,
        message=f"Indexing complete. Found {snapshot.file_count} files and {snapshot.symbol_count} symbols.",
        git_branch=snapshot.git_branch,
        git_commit=snapshot.git_commit,
    )


@router.post("/{project_id}/snapshots/branch", response_model=SnapshotResponse)
async def create_branch_snapshot(
    project_id: str,
    request: BranchSnapshotRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a snapshot for a specific git branch"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.root_path:
        raise HTTPException(status_code=400, detail="Project has no root path configured")

    # Verify git repo and branch exists
    git = GitService(project.root_path)
    if not git.is_git_repo():
        raise HTTPException(status_code=400, detail="Project is not a git repository")
    
    # Get available branches
    branches = git.get_branches()
    branch_names = [b.name for b in branches]
    if request.branch not in branch_names:
        raise HTTPException(
            status_code=400,
            detail=f"Branch '{request.branch}' not found. Available: {', '.join(branch_names)}"
        )
    
    # Stash any current changes and checkout the branch
    current_branch = git.get_current_branch()
    status = git.get_status()
    stashed = False
    
    try:
        if status.has_changes:
            stashed = git.stash_changes(f"CodeAtlas snapshot for {request.branch}")
        
        if current_branch != request.branch:
            git.checkout_branch(request.branch)
        
        git_commit = git.get_current_commit()
        
        # Run indexing
        engine = IndexingEngine(db)
        snapshot = await engine.index_project(
            project_id,
            git_branch=request.branch,
            git_commit=git_commit
        )
        
    finally:
        # Restore original state
        if current_branch and current_branch != request.branch:
            git.checkout_branch(current_branch)
        if stashed:
            git.stash_pop()

    return SnapshotResponse(
        snapshot_id=snapshot.id,
        status=snapshot.status.value,
        message=f"Branch '{request.branch}' indexed. Found {snapshot.file_count} files and {snapshot.symbol_count} symbols.",
        git_branch=snapshot.git_branch,
        git_commit=snapshot.git_commit,
    )


@router.get("/{project_id}/snapshots", response_model=List[SnapshotResponse])
async def list_project_snapshots(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """List all snapshots for a project"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    result = await db.execute(
        select(Snapshot)
        .where(Snapshot.project_id == project_id)
        .order_by(Snapshot.created_at.desc())
    )
    snapshots = result.scalars().all()

    return [
        SnapshotResponse(
            snapshot_id=s.id,
            status=s.status.value,
            message=f"{s.file_count} files, {s.symbol_count} symbols",
            git_branch=s.git_branch,
            git_commit=s.git_commit,
        )
        for s in snapshots
    ]
