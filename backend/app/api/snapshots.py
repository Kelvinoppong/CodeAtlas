"""
Snapshot endpoints
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter()


class SnapshotStatus(BaseModel):
    id: str
    project_id: str
    status: str  # pending, indexing, ready, failed
    git_commit: Optional[str]
    created_at: datetime
    file_count: int = 0
    symbol_count: int = 0
    progress: float = 0.0  # 0-100


class FileTreeNode(BaseModel):
    name: str
    path: str
    type: str  # file or folder
    language: Optional[str] = None
    children: Optional[List["FileTreeNode"]] = None


# Demo data
_demo_tree: List[FileTreeNode] = [
    FileTreeNode(
        name="DoubleClickMe.md",
        path="/DoubleClickMe.md",
        type="file",
        language="markdown",
    ),
    FileTreeNode(
        name="minesweeper",
        path="/minesweeper",
        type="folder",
        children=[
            FileTreeNode(
                name="__pycache__",
                path="/minesweeper/__pycache__",
                type="folder",
                children=[
                    FileTreeNode(
                        name="minesweeper.cpython-312.pyc",
                        path="/minesweeper/__pycache__/minesweeper.cpython-312.pyc",
                        type="file",
                    ),
                ],
            ),
            FileTreeNode(
                name="assets",
                path="/minesweeper/assets",
                type="folder",
                children=[
                    FileTreeNode(
                        name="fonts",
                        path="/minesweeper/assets/fonts",
                        type="folder",
                        children=[
                            FileTreeNode(
                                name="OpenSans-Regular.ttf",
                                path="/minesweeper/assets/fonts/OpenSans-Regular.ttf",
                                type="file",
                            ),
                        ],
                    ),
                    FileTreeNode(
                        name="images",
                        path="/minesweeper/assets/images",
                        type="folder",
                        children=[
                            FileTreeNode(
                                name="flag.png",
                                path="/minesweeper/assets/images/flag.png",
                                type="file",
                                language="image",
                            ),
                            FileTreeNode(
                                name="mine.png",
                                path="/minesweeper/assets/images/mine.png",
                                type="file",
                                language="image",
                            ),
                        ],
                    ),
                ],
            ),
            FileTreeNode(
                name="minesweeper.py",
                path="/minesweeper/minesweeper.py",
                type="file",
                language="python",
            ),
        ],
    ),
]


@router.get("/{snapshot_id}/status", response_model=SnapshotStatus)
async def get_snapshot_status(snapshot_id: str):
    """Get snapshot indexing status"""
    # Demo response
    return SnapshotStatus(
        id=snapshot_id,
        project_id="demo",
        status="ready",
        git_commit=None,
        created_at=datetime.utcnow(),
        file_count=5,
        symbol_count=12,
        progress=100.0,
    )


@router.get("/{snapshot_id}/tree", response_model=List[FileTreeNode])
async def get_file_tree(snapshot_id: str):
    """Get the file tree for a snapshot"""
    return _demo_tree


@router.get("/{snapshot_id}/graphs/deps")
async def get_dependency_graph(snapshot_id: str, path: Optional[str] = None):
    """Get dependency graph for a file or module"""
    # Demo graph data
    return {
        "nodes": [
            {"id": "main", "label": "main", "type": "function"},
            {"id": "init", "label": "__init__", "type": "method"},
            {"id": "board", "label": "board", "type": "attribute"},
            {"id": "mines", "label": "mines", "type": "attribute"},
            {"id": "print", "label": "print", "type": "method"},
        ],
        "edges": [
            {"source": "main", "target": "init"},
            {"source": "init", "target": "board"},
            {"source": "init", "target": "mines"},
            {"source": "main", "target": "print"},
        ],
    }


@router.get("/{snapshot_id}/graphs/calls")
async def get_call_graph(snapshot_id: str, symbol_id: Optional[str] = None):
    """Get call graph for a symbol"""
    return {
        "nodes": [],
        "edges": [],
        "message": "Call graph analysis not yet implemented",
    }
