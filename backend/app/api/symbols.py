"""
Symbol search and references endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.core.database import get_db
from app.models.symbol import Symbol, Reference, SymbolKind, ReferenceKind
from app.models.file import File

router = APIRouter()


class SymbolResponse(BaseModel):
    id: str
    name: str
    kind: str
    file_path: str
    start_line: int
    end_line: int
    signature: Optional[str] = None
    docstring: Optional[str] = None
    parent_id: Optional[str] = None


class ReferenceResponse(BaseModel):
    file_path: str
    line: int
    column: int
    kind: str


@router.get("", response_model=List[SymbolResponse])
async def search_symbols(
    snapshot_id: str,
    query: Optional[str] = Query(None),
    kind: Optional[str] = Query(None),
    file_path: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
):
    """Search for symbols in the codebase"""
    # Build query
    stmt = select(Symbol, File).join(File, Symbol.file_id == File.id).where(
        Symbol.snapshot_id == snapshot_id
    )

    if query:
        stmt = stmt.where(
            or_(
                Symbol.name.ilike(f"%{query}%"),
                Symbol.qualified_name.ilike(f"%{query}%"),
            )
        )

    if kind:
        try:
            symbol_kind = SymbolKind(kind)
            stmt = stmt.where(Symbol.kind == symbol_kind)
        except ValueError:
            pass  # Invalid kind, ignore filter

    if file_path:
        stmt = stmt.where(File.path == file_path)

    stmt = stmt.limit(limit)

    result = await db.execute(stmt)
    rows = result.all()

    return [
        SymbolResponse(
            id=symbol.id,
            name=symbol.name,
            kind=symbol.kind.value,
            file_path=file.path,
            start_line=symbol.start_line,
            end_line=symbol.end_line,
            signature=symbol.signature,
            docstring=symbol.docstring,
            parent_id=symbol.parent_id,
        )
        for symbol, file in rows
    ]


@router.get("/{symbol_id}", response_model=SymbolResponse)
async def get_symbol(
    snapshot_id: str,
    symbol_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get symbol details"""
    result = await db.execute(
        select(Symbol, File)
        .join(File, Symbol.file_id == File.id)
        .where(Symbol.id == symbol_id, Symbol.snapshot_id == snapshot_id)
    )
    row = result.one_or_none()

    if not row:
        raise HTTPException(status_code=404, detail="Symbol not found")

    symbol, file = row

    return SymbolResponse(
        id=symbol.id,
        name=symbol.name,
        kind=symbol.kind.value,
        file_path=file.path,
        start_line=symbol.start_line,
        end_line=symbol.end_line,
        signature=symbol.signature,
        docstring=symbol.docstring,
        parent_id=symbol.parent_id,
    )


@router.get("/{symbol_id}/references", response_model=List[ReferenceResponse])
async def get_references(
    snapshot_id: str,
    symbol_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get all references to a symbol"""
    result = await db.execute(
        select(Reference, Symbol, File)
        .join(Symbol, Reference.from_symbol_id == Symbol.id)
        .join(File, Symbol.file_id == File.id)
        .where(
            Reference.to_symbol_id == symbol_id,
            Reference.snapshot_id == snapshot_id,
        )
    )
    rows = result.all()

    return [
        ReferenceResponse(
            file_path=file.path,
            line=ref.line,
            column=ref.column,
            kind=ref.kind.value,
        )
        for ref, symbol, file in rows
    ]


@router.get("/kinds/list")
async def list_symbol_kinds():
    """List all available symbol kinds"""
    return [kind.value for kind in SymbolKind]
