"""
Impact Analysis API - "What breaks if I change this?"

This endpoint exposes the change impact analysis functionality,
allowing users to understand the ripple effects of code changes
before making them.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.symbol import Symbol
from app.models.file import File
from app.services.impact_analyzer import (
    ImpactAnalyzer,
    ImpactAnalysis as ImpactAnalysisResult,
)

router = APIRouter()


# Request/Response Models

class AnalyzeFileRequest(BaseModel):
    """Request to analyze impact of changing files"""
    file_paths: List[str] = Field(..., description="List of file paths being changed")
    max_depth: int = Field(3, ge=1, le=10, description="Maximum depth for transitive analysis")


class AnalyzeSymbolRequest(BaseModel):
    """Request to analyze impact of changing symbols"""
    symbol_ids: List[str] = Field(..., description="List of symbol IDs being changed")
    max_depth: int = Field(3, ge=1, le=10, description="Maximum depth for transitive analysis")


class ImpactPathResponse(BaseModel):
    """Path from changed symbol to impacted symbol"""
    symbols: List[str]
    symbol_names: List[str]
    reference_kinds: List[str]


class ImpactedSymbolResponse(BaseModel):
    """A symbol affected by the change"""
    id: str
    name: str
    kind: str
    file_path: str
    start_line: int
    end_line: int
    impact_type: str  # "changed", "direct", "transitive"
    distance: int
    reference_kind: Optional[str] = None
    reference_context: Optional[str] = None
    reference_line: Optional[int] = None
    impact_path: Optional[ImpactPathResponse] = None


class ImpactedFileResponse(BaseModel):
    """A file containing affected symbols"""
    path: str
    language: Optional[str] = None
    symbols_affected: List[ImpactedSymbolResponse]
    is_directly_changed: bool
    direct_impact_count: int
    transitive_impact_count: int


class GraphNodeResponse(BaseModel):
    """Node in the impact graph"""
    id: str
    name: str
    kind: str
    file_path: str
    line: int
    node_type: str  # "changed", "direct", "transitive"
    distance: int


class GraphEdgeResponse(BaseModel):
    """Edge in the impact graph"""
    source: str
    target: str
    kind: str
    label: str
    context: Optional[str] = None


class ImpactGraphResponse(BaseModel):
    """Graph data for visualization"""
    nodes: List[GraphNodeResponse]
    edges: List[GraphEdgeResponse]


class ImpactAnalysisResponse(BaseModel):
    """Complete impact analysis result"""
    changed_files: List[str]
    changed_symbols: List[ImpactedSymbolResponse]
    impacted_files: List[ImpactedFileResponse]
    impacted_symbols: List[ImpactedSymbolResponse]
    total_files_affected: int
    total_symbols_affected: int
    risk_level: str  # "low", "medium", "high", "critical"
    risk_score: float
    risk_explanation: str
    impact_graph: ImpactGraphResponse
    circular_dependencies: List[List[str]]


class ImpactPreviewResponse(BaseModel):
    """Lightweight preview for hover/quick check"""
    total_dependents: int
    direct_dependents: int
    transitive_dependents: int
    risk_level: str
    affected_files_count: int


# Helper functions

def _convert_impact_path(path) -> Optional[ImpactPathResponse]:
    """Convert internal ImpactPath to response model"""
    if path is None:
        return None
    return ImpactPathResponse(
        symbols=path.symbols,
        symbol_names=path.symbol_names,
        reference_kinds=path.reference_kinds,
    )


def _convert_impacted_symbol(sym) -> ImpactedSymbolResponse:
    """Convert internal ImpactedSymbol to response model"""
    return ImpactedSymbolResponse(
        id=sym.id,
        name=sym.name,
        kind=sym.kind,
        file_path=sym.file_path,
        start_line=sym.start_line,
        end_line=sym.end_line,
        impact_type=sym.impact_type,
        distance=sym.distance,
        reference_kind=sym.reference_kind,
        reference_context=sym.reference_context,
        reference_line=sym.reference_line,
        impact_path=_convert_impact_path(sym.impact_path),
    )


def _convert_analysis_result(result: ImpactAnalysisResult) -> ImpactAnalysisResponse:
    """Convert internal ImpactAnalysis to API response"""
    return ImpactAnalysisResponse(
        changed_files=result.changed_files,
        changed_symbols=[_convert_impacted_symbol(s) for s in result.changed_symbols],
        impacted_files=[
            ImpactedFileResponse(
                path=f.path,
                language=f.language,
                symbols_affected=[_convert_impacted_symbol(s) for s in f.symbols_affected],
                is_directly_changed=f.is_directly_changed,
                direct_impact_count=f.direct_impact_count,
                transitive_impact_count=f.transitive_impact_count,
            )
            for f in result.impacted_files
        ],
        impacted_symbols=[_convert_impacted_symbol(s) for s in result.impacted_symbols],
        total_files_affected=result.total_files_affected,
        total_symbols_affected=result.total_symbols_affected,
        risk_level=result.risk_level,
        risk_score=result.risk_score,
        risk_explanation=result.risk_explanation,
        impact_graph=ImpactGraphResponse(
            nodes=[
                GraphNodeResponse(
                    id=n.id,
                    name=n.name,
                    kind=n.kind,
                    file_path=n.file_path,
                    line=n.line,
                    node_type=n.node_type,
                    distance=n.distance,
                )
                for n in result.impact_graph.nodes
            ],
            edges=[
                GraphEdgeResponse(
                    source=e.source,
                    target=e.target,
                    kind=e.kind,
                    label=e.label,
                    context=e.context,
                )
                for e in result.impact_graph.edges
            ],
        ),
        circular_dependencies=result.circular_dependencies,
    )


# Endpoints

@router.post("/analyze-files", response_model=ImpactAnalysisResponse)
async def analyze_file_impact(
    snapshot_id: str,
    request: AnalyzeFileRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Analyze the impact of changing specified files.
    
    Returns a complete analysis including:
    - All symbols that would be affected
    - Files containing affected symbols
    - Risk assessment
    - Graph data for visualization
    - Detected circular dependencies
    """
    # Verify files exist
    for file_path in request.file_paths:
        result = await db.execute(
            select(File).where(
                File.snapshot_id == snapshot_id,
                File.path == file_path,
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {file_path}"
            )
    
    analyzer = ImpactAnalyzer(db, snapshot_id)
    result = await analyzer.analyze_file_changes(
        request.file_paths,
        max_depth=request.max_depth,
    )
    
    return _convert_analysis_result(result)


@router.post("/analyze-symbols", response_model=ImpactAnalysisResponse)
async def analyze_symbol_impact(
    snapshot_id: str,
    request: AnalyzeSymbolRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Analyze the impact of changing specified symbols.
    
    This is more precise than file-level analysis, allowing you to
    see the impact of changing a specific function, class, or variable.
    """
    # Verify symbols exist
    for symbol_id in request.symbol_ids:
        result = await db.execute(
            select(Symbol).where(
                Symbol.snapshot_id == snapshot_id,
                Symbol.id == symbol_id,
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=404,
                detail=f"Symbol not found: {symbol_id}"
            )
    
    analyzer = ImpactAnalyzer(db, snapshot_id)
    result = await analyzer.analyze_symbol_changes(
        request.symbol_ids,
        max_depth=request.max_depth,
    )
    
    return _convert_analysis_result(result)


@router.get("/preview", response_model=ImpactPreviewResponse)
async def preview_impact(
    snapshot_id: str,
    path: str = Query(..., description="File path"),
    line: int = Query(..., description="Line number in the file"),
    db: AsyncSession = Depends(get_db),
):
    """
    Quick impact preview for a symbol at a specific location.
    
    Useful for hover tooltips and status bar indicators.
    Returns a lightweight summary without the full graph data.
    """
    # Find the symbol at this location
    result = await db.execute(
        select(Symbol)
        .join(File)
        .where(
            Symbol.snapshot_id == snapshot_id,
            File.path == path,
            Symbol.start_line <= line,
            Symbol.end_line >= line,
        )
        .order_by(
            # Prefer the most specific (smallest) symbol
            (Symbol.end_line - Symbol.start_line)
        )
        .limit(1)
    )
    symbol = result.scalar_one_or_none()
    
    if not symbol:
        # No symbol at this location
        return ImpactPreviewResponse(
            total_dependents=0,
            direct_dependents=0,
            transitive_dependents=0,
            risk_level="low",
            affected_files_count=0,
        )
    
    # Run quick analysis
    analyzer = ImpactAnalyzer(db, snapshot_id)
    analysis = await analyzer.analyze_symbol_changes([symbol.id], max_depth=2)
    
    direct_count = sum(
        1 for s in analysis.impacted_symbols
        if s.impact_type == "direct"
    )
    transitive_count = len(analysis.impacted_symbols) - direct_count
    
    return ImpactPreviewResponse(
        total_dependents=len(analysis.impacted_symbols),
        direct_dependents=direct_count,
        transitive_dependents=transitive_count,
        risk_level=analysis.risk_level,
        affected_files_count=len(analysis.impacted_files),
    )


@router.get("/symbol/{symbol_id}", response_model=ImpactAnalysisResponse)
async def get_symbol_impact(
    snapshot_id: str,
    symbol_id: str,
    max_depth: int = Query(3, ge=1, le=10),
    db: AsyncSession = Depends(get_db),
):
    """
    Get impact analysis for a specific symbol by ID.
    
    Convenience endpoint for direct symbol lookup.
    """
    # Verify symbol exists
    result = await db.execute(
        select(Symbol).where(
            Symbol.snapshot_id == snapshot_id,
            Symbol.id == symbol_id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Symbol not found")
    
    analyzer = ImpactAnalyzer(db, snapshot_id)
    analysis = await analyzer.analyze_symbol_changes([symbol_id], max_depth=max_depth)
    
    return _convert_analysis_result(analysis)
