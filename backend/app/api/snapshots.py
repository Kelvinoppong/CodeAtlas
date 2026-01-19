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
from app.indexer.engine import IndexingEngine

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
