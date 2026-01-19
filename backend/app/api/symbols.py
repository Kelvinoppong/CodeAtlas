"""
Symbol search and references endpoints
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter()


class Symbol(BaseModel):
    id: str
    name: str
    kind: str  # function, class, method, variable, module
    file_path: str
    start_line: int
    end_line: int
    signature: Optional[str] = None
    docstring: Optional[str] = None


class Reference(BaseModel):
    file_path: str
    line: int
    column: int
    kind: str  # import, call, usage


# Demo symbols
_demo_symbols = [
    Symbol(
        id="1",
        name="Minesweeper",
        kind="class",
        file_path="/minesweeper/minesweeper.py",
        start_line=4,
        end_line=75,
        signature="class Minesweeper()",
        docstring="Minesweeper game representation",
    ),
    Symbol(
        id="2",
        name="__init__",
        kind="method",
        file_path="/minesweeper/minesweeper.py",
        start_line=9,
        end_line=34,
        signature="def __init__(self, height=8, width=8, mines=8)",
    ),
    Symbol(
        id="3",
        name="print",
        kind="method",
        file_path="/minesweeper/minesweeper.py",
        start_line=36,
        end_line=49,
        signature="def print(self)",
        docstring="Prints a text-based representation of where mines are located.",
    ),
    Symbol(
        id="4",
        name="is_mine",
        kind="method",
        file_path="/minesweeper/minesweeper.py",
        start_line=51,
        end_line=53,
        signature="def is_mine(self, cell)",
    ),
    Symbol(
        id="5",
        name="nearby_mines",
        kind="method",
        file_path="/minesweeper/minesweeper.py",
        start_line=55,
        end_line=68,
        signature="def nearby_mines(self, cell)",
        docstring="Returns the number of mines within one row and column of a given cell.",
    ),
    Symbol(
        id="6",
        name="won",
        kind="method",
        file_path="/minesweeper/minesweeper.py",
        start_line=70,
        end_line=75,
        signature="def won(self)",
        docstring="Checks if all mines have been flagged.",
    ),
]


@router.get("", response_model=List[Symbol])
async def search_symbols(
    snapshot_id: str,
    query: Optional[str] = Query(None),
    kind: Optional[str] = Query(None),
):
    """Search for symbols in the codebase"""
    results = _demo_symbols
    
    if query:
        query_lower = query.lower()
        results = [s for s in results if query_lower in s.name.lower()]
    
    if kind:
        results = [s for s in results if s.kind == kind]
    
    return results


@router.get("/{symbol_id}", response_model=Symbol)
async def get_symbol(snapshot_id: str, symbol_id: str):
    """Get symbol details"""
    for s in _demo_symbols:
        if s.id == symbol_id:
            return s
    return None


@router.get("/{symbol_id}/references", response_model=List[Reference])
async def get_references(snapshot_id: str, symbol_id: str):
    """Get all references to a symbol"""
    # Demo references
    return [
        Reference(
            file_path="/minesweeper/minesweeper.py",
            line=15,
            column=8,
            kind="usage",
        ),
        Reference(
            file_path="/minesweeper/minesweeper.py",
            line=25,
            column=12,
            kind="usage",
        ),
    ]
