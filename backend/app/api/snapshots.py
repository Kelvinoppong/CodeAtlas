"""
Snapshot endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.snapshot import Snapshot, SnapshotStatus
from app.models.file import File
from app.models.project import Project
from app.indexer.engine import IndexingEngine
from app.services.impact_analyzer import ImpactAnalyzer
from app.services.git_service import GitService

router = APIRouter()


class SnapshotStatusResponse(BaseModel):
    id: str
    project_id: str
    status: str
    git_commit: Optional[str]
    created_at: datetime
    file_count: int
    symbol_count: int
    total_lines: int
    progress: float
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class FileTreeNode(BaseModel):
    name: str
    path: str
    type: str
    language: Optional[str] = None
    size: Optional[int] = None
    children: Optional[List["FileTreeNode"]] = None


FileTreeNode.model_rebuild()


@router.get("/{snapshot_id}/status", response_model=SnapshotStatusResponse)
async def get_snapshot_status(
    snapshot_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get snapshot indexing status"""
    result = await db.execute(select(Snapshot).where(Snapshot.id == snapshot_id))
    snapshot = result.scalar_one_or_none()

    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    return SnapshotStatusResponse(
        id=snapshot.id,
        project_id=snapshot.project_id,
        status=snapshot.status.value,
        git_commit=snapshot.git_commit,
        created_at=snapshot.created_at,
        file_count=snapshot.file_count,
        symbol_count=snapshot.symbol_count,
        total_lines=snapshot.total_lines,
        progress=snapshot.progress,
        error_message=snapshot.error_message,
    )


@router.get("/{snapshot_id}/tree")
async def get_file_tree(
    snapshot_id: str,
    db: AsyncSession = Depends(get_db),
) -> List[Any]:
    """Get the file tree for a snapshot"""
    result = await db.execute(select(Snapshot).where(Snapshot.id == snapshot_id))
    snapshot = result.scalar_one_or_none()

    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    engine = IndexingEngine(db)
    tree = await engine.build_file_tree(snapshot_id)

    return tree.get("children", [])


@router.get("/{snapshot_id}/graphs/deps")
async def get_dependency_graph(
    snapshot_id: str,
    path: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get dependency graph for a file or the whole project"""
    result = await db.execute(select(Snapshot).where(Snapshot.id == snapshot_id))
    snapshot = result.scalar_one_or_none()

    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    engine = IndexingEngine(db)
    graph = await engine.get_dependency_graph(snapshot_id, file_path=path)

    return graph


@router.get("/{snapshot_id}/graphs/calls")
async def get_call_graph(
    snapshot_id: str,
    symbol_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get call graph for a symbol"""
    # TODO: Implement call graph analysis
    return {
        "nodes": [],
        "edges": [],
        "message": "Call graph analysis coming soon",
    }


# ============ Impact Analysis ============

class ImpactAnalysisRequest(BaseModel):
    files: Optional[List[str]] = None
    symbol_ids: Optional[List[str]] = None


class ImpactedSymbolResponse(BaseModel):
    id: str
    name: str
    kind: str
    file_path: str
    start_line: int
    end_line: int
    impact_type: str
    distance: int


class ImpactedFileResponse(BaseModel):
    path: str
    language: Optional[str]
    symbols_affected: List[ImpactedSymbolResponse]
    is_directly_changed: bool


class ImpactAnalysisResponse(BaseModel):
    changed_files: List[str]
    changed_symbols: List[ImpactedSymbolResponse]
    impacted_files: List[ImpactedFileResponse]
    impacted_symbols: List[ImpactedSymbolResponse]
    total_files_affected: int
    total_symbols_affected: int
    risk_level: str
    risk_explanation: str


@router.post("/{snapshot_id}/impact", response_model=ImpactAnalysisResponse)
async def analyze_impact(
    snapshot_id: str,
    request: ImpactAnalysisRequest,
    db: AsyncSession = Depends(get_db),
):
    """Analyze the impact of changing files or symbols"""
    result = await db.execute(select(Snapshot).where(Snapshot.id == snapshot_id))
    snapshot = result.scalar_one_or_none()
    
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    
    analyzer = ImpactAnalyzer(db, snapshot_id)
    
    if request.files:
        analysis = await analyzer.analyze_file_changes(request.files)
    elif request.symbol_ids:
        analysis = await analyzer.analyze_symbol_changes(request.symbol_ids)
    else:
        raise HTTPException(
            status_code=400,
            detail="Either 'files' or 'symbol_ids' must be provided"
        )
    
    return ImpactAnalysisResponse(
        changed_files=analysis.changed_files,
        changed_symbols=[
            ImpactedSymbolResponse(
                id=s.id,
                name=s.name,
                kind=s.kind,
                file_path=s.file_path,
                start_line=s.start_line,
                end_line=s.end_line,
                impact_type=s.impact_type,
                distance=s.distance,
            )
            for s in analysis.changed_symbols
        ],
        impacted_files=[
            ImpactedFileResponse(
                path=f.path,
                language=f.language,
                symbols_affected=[
                    ImpactedSymbolResponse(
                        id=s.id,
                        name=s.name,
                        kind=s.kind,
                        file_path=s.file_path,
                        start_line=s.start_line,
                        end_line=s.end_line,
                        impact_type=s.impact_type,
                        distance=s.distance,
                    )
                    for s in f.symbols_affected
                ],
                is_directly_changed=f.is_directly_changed,
            )
            for f in analysis.impacted_files
        ],
        impacted_symbols=[
            ImpactedSymbolResponse(
                id=s.id,
                name=s.name,
                kind=s.kind,
                file_path=s.file_path,
                start_line=s.start_line,
                end_line=s.end_line,
                impact_type=s.impact_type,
                distance=s.distance,
            )
            for s in analysis.impacted_symbols
        ],
        total_files_affected=analysis.total_files_affected,
        total_symbols_affected=analysis.total_symbols_affected,
        risk_level=analysis.risk_level,
        risk_explanation=analysis.risk_explanation,
    )


# ============ Git Integration ============

class GitBranchResponse(BaseModel):
    name: str
    is_current: bool
    commit_sha: str
    last_commit_message: str


class GitStatusResponse(BaseModel):
    is_repo: bool
    branch: Optional[str]
    has_changes: bool
    staged_files: List[str]
    modified_files: List[str]
    untracked_files: List[str]


class GitCommitResponse(BaseModel):
    sha: str
    short_sha: str
    message: str
    author: str
    author_email: str
    date: datetime


@router.get("/{snapshot_id}/git/status", response_model=GitStatusResponse)
async def get_git_status(
    snapshot_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get git status for the project"""
    # Get project path from snapshot
    result = await db.execute(
        select(Snapshot, Project)
        .join(Project)
        .where(Snapshot.id == snapshot_id)
    )
    row = result.one_or_none()
    
    if not row:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    
    snapshot, project = row
    
    if not project.root_path:
        raise HTTPException(status_code=400, detail="Project has no root path")
    
    git = GitService(project.root_path)
    status = git.get_status()
    
    return GitStatusResponse(
        is_repo=status.is_repo,
        branch=status.branch,
        has_changes=status.has_changes,
        staged_files=status.staged_files,
        modified_files=status.modified_files,
        untracked_files=status.untracked_files,
    )


@router.get("/{snapshot_id}/git/branches", response_model=List[GitBranchResponse])
async def get_git_branches(
    snapshot_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get git branches for the project"""
    result = await db.execute(
        select(Snapshot, Project)
        .join(Project)
        .where(Snapshot.id == snapshot_id)
    )
    row = result.one_or_none()
    
    if not row:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    
    snapshot, project = row
    
    if not project.root_path:
        raise HTTPException(status_code=400, detail="Project has no root path")
    
    git = GitService(project.root_path)
    branches = git.get_branches()
    
    return [
        GitBranchResponse(
            name=b.name,
            is_current=b.is_current,
            commit_sha=b.commit_sha,
            last_commit_message=b.last_commit_message,
        )
        for b in branches
    ]


@router.get("/{snapshot_id}/git/commits", response_model=List[GitCommitResponse])
async def get_git_commits(
    snapshot_id: str,
    limit: int = Query(50, ge=1, le=200),
    branch: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get recent git commits for the project"""
    result = await db.execute(
        select(Snapshot, Project)
        .join(Project)
        .where(Snapshot.id == snapshot_id)
    )
    row = result.one_or_none()
    
    if not row:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    
    snapshot, project = row
    
    if not project.root_path:
        raise HTTPException(status_code=400, detail="Project has no root path")
    
    git = GitService(project.root_path)
    commits = git.get_commits(limit=limit, branch=branch)
    
    return [
        GitCommitResponse(
            sha=c.sha,
            short_sha=c.short_sha,
            message=c.message,
            author=c.author,
            author_email=c.author_email,
            date=c.date,
        )
        for c in commits
    ]
