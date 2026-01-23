"""
System endpoints - directory browsing, system info
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from pathlib import Path
import os

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
                # Only show directories for project selection
                if is_dir:
                    entries.append(DirectoryEntry(
                        name=item.name,
                        path=str(item.resolve()),
                        is_dir=is_dir,
                    ))
            except PermissionError:
                continue
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Sort alphabetically
    entries.sort(key=lambda x: x.name.lower())
    
    # Get parent path
    parent_path = str(target_path.parent) if target_path.parent != target_path else None
    
    return BrowseResponse(
        current_path=str(target_path.resolve()),
        parent_path=parent_path,
        entries=entries,
    )
