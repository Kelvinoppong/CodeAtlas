"""
File content endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List
from pathlib import Path
import os

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.snapshot import Snapshot
from app.models.file import File
from app.models.project import Project

router = APIRouter()


class DirectoryEntry(BaseModel):
    name: str
    path: str
    is_dir: bool


class BrowseResponse(BaseModel):
    current_path: str
    parent_path: Optional[str]
    entries: List[DirectoryEntry]


@router.get("/browse", response_model=BrowseResponse)
async def browse_directory(
    path: str = Query(default="~", description="Directory path to browse"),
):
    """Browse local directories for project import"""
    # Expand ~ to home directory
    expanded_path = os.path.expanduser(path)
    target_path = Path(expanded_path)
    
    # Default to home if path doesn't exist
    if not target_path.exists():
        target_path = Path.home()
    
    # Must be a directory
    if not target_path.is_dir():
        target_path = target_path.parent
    
    entries = []
    try:
        for item in sorted(target_path.iterdir()):
            # Skip hidden files/dirs (starting with .)
            if item.name.startswith('.'):
                continue
            # Skip common non-project directories
            if item.name in ['node_modules', '__pycache__', 'venv', '.git', 'dist', 'build']:
                continue
            try:
                is_dir = item.is_dir()
                entries.append(DirectoryEntry(
                    name=item.name,
                    path=str(item.resolve()),
                    is_dir=is_dir,
                ))
            except PermissionError:
                continue
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Sort: directories first, then files
    entries.sort(key=lambda x: (not x.is_dir, x.name.lower()))
    
    # Get parent path
    parent_path = str(target_path.parent) if target_path.parent != target_path else None
    
    return BrowseResponse(
        current_path=str(target_path.resolve()),
        parent_path=parent_path,
        entries=entries,
    )


class FileContentResponse(BaseModel):
    path: str
    content: str
    language: Optional[str]
    size_bytes: int
    line_count: int


@router.get("", response_model=FileContentResponse)
async def get_file_content(
    snapshot_id: str,
    path: str = Query(..., description="File path relative to project root"),
    db: AsyncSession = Depends(get_db),
):
    """Get file content by path"""
    # Get snapshot
    result = await db.execute(select(Snapshot).where(Snapshot.id == snapshot_id))
    snapshot = result.scalar_one_or_none()

    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    # Get file record
    result = await db.execute(
        select(File).where(
            File.snapshot_id == snapshot_id,
            File.path == path,
        )
    )
    file_record = result.scalar_one_or_none()

    if not file_record:
        raise HTTPException(status_code=404, detail=f"File not found: {path}")

    # Get content - from cache or read from disk
    content = file_record.content

    if not content:
        # Read from disk
        result = await db.execute(
            select(Project).where(Project.id == snapshot.project_id)
        )
        project = result.scalar_one_or_none()

        if project and project.root_path:
            file_path = Path(project.root_path) / path
            if file_path.exists() and file_path.is_file():
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"Could not read file: {e}")
            else:
                raise HTTPException(status_code=404, detail="File not found on disk")
        else:
            raise HTTPException(status_code=404, detail="Project root path not configured")

    return FileContentResponse(
        path=path,
        content=content,
        language=file_record.language,
        size_bytes=file_record.size_bytes,
        line_count=file_record.line_count,
    )


@router.get("/list")
async def list_files(
    snapshot_id: str,
    language: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List all files in a snapshot"""
    query = select(File).where(File.snapshot_id == snapshot_id)

    if language:
        query = query.where(File.language == language)

    result = await db.execute(query)
    files = result.scalars().all()

    return [
        {
            "id": f.id,
            "path": f.path,
            "language": f.language,
            "size_bytes": f.size_bytes,
            "line_count": f.line_count,
            "is_binary": f.is_binary,
        }
        for f in files
    ]
