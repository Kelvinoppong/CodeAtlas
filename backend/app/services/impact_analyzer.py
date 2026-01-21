"""
Impact Analyzer - Analyzes what breaks when code changes
"""

from dataclasses import dataclass, field
from typing import List, Set, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.symbol import Symbol, Reference
from app.models.file import File


@dataclass
class ImpactedSymbol:
    id: str
    name: str
    kind: str
    file_path: str
    start_line: int
    end_line: int
    impact_type: str  # "direct" or "transitive"
    distance: int  # How many hops from the changed symbol


@dataclass
class ImpactedFile:
    path: str
    language: Optional[str]
    symbols_affected: List[ImpactedSymbol] = field(default_factory=list)
    is_directly_changed: bool = False


@dataclass
class ImpactAnalysis:
    changed_files: List[str]
    changed_symbols: List[ImpactedSymbol]
    impacted_files: List[ImpactedFile]
    impacted_symbols: List[ImpactedSymbol]
    total_files_affected: int
    total_symbols_affected: int
    risk_level: str  # "low", "medium", "high", "critical"
    risk_explanation: str


class ImpactAnalyzer:
    """Analyzes the impact of code changes across the codebase"""
    
    def __init__(self, db: AsyncSession, snapshot_id: str):
        self.db = db
        self.snapshot_id = snapshot_id
    
    async def analyze_file_changes(self, file_paths: List[str]) -> ImpactAnalysis:
        """Analyze the impact of changing specified files"""
        # Get all symbols in the changed files
        result = await self.db.execute(
            select(Symbol)
            .join(File)
            .where(
                Symbol.snapshot_id == self.snapshot_id,
                File.path.in_(file_paths)
            )
        )
        changed_symbols = result.scalars().all()
        
        changed_symbol_data = [
            ImpactedSymbol(
                id=s.id,
                name=s.name,
                kind=s.kind,
                file_path=s.file.path if s.file else "",
                start_line=s.start_line,
                end_line=s.end_line,
                impact_type="direct",
                distance=0,
            )
            for s in changed_symbols
        ]
        
        # Find all references to these symbols
        symbol_ids = [s.id for s in changed_symbols]
        impacted_symbols, impacted_files = await self._trace_impact(symbol_ids)
        
        # Calculate risk level
        risk_level, risk_explanation = self._calculate_risk(
            len(file_paths),
            len(changed_symbols),
            len(impacted_files),
            len(impacted_symbols),
        )
        
        return ImpactAnalysis(
            changed_files=file_paths,
            changed_symbols=changed_symbol_data,
            impacted_files=impacted_files,
            impacted_symbols=impacted_symbols,
            total_files_affected=len(impacted_files) + len(file_paths),
            total_symbols_affected=len(impacted_symbols) + len(changed_symbols),
            risk_level=risk_level,
            risk_explanation=risk_explanation,
        )
    
    async def analyze_symbol_changes(self, symbol_ids: List[str]) -> ImpactAnalysis:
        """Analyze the impact of changing specified symbols"""
        # Get the symbols
        result = await self.db.execute(
            select(Symbol)
            .options(selectinload(Symbol.file))
            .where(
                Symbol.id.in_(symbol_ids),
                Symbol.snapshot_id == self.snapshot_id,
            )
        )
        symbols = result.scalars().all()
        
        changed_files = list(set(s.file.path for s in symbols if s.file))
        changed_symbol_data = [
            ImpactedSymbol(
                id=s.id,
                name=s.name,
                kind=s.kind,
                file_path=s.file.path if s.file else "",
                start_line=s.start_line,
                end_line=s.end_line,
                impact_type="direct",
                distance=0,
            )
            for s in symbols
        ]
        
        # Trace impact
        impacted_symbols, impacted_files = await self._trace_impact(symbol_ids)
        
        # Calculate risk
        risk_level, risk_explanation = self._calculate_risk(
            len(changed_files),
            len(symbols),
            len(impacted_files),
            len(impacted_symbols),
        )
        
        return ImpactAnalysis(
            changed_files=changed_files,
            changed_symbols=changed_symbol_data,
            impacted_files=impacted_files,
            impacted_symbols=impacted_symbols,
            total_files_affected=len(impacted_files) + len(changed_files),
            total_symbols_affected=len(impacted_symbols) + len(symbols),
            risk_level=risk_level,
            risk_explanation=risk_explanation,
        )
    
    async def _trace_impact(
        self,
        symbol_ids: List[str],
        max_depth: int = 3
    ) -> tuple[List[ImpactedSymbol], List[ImpactedFile]]:
        """Trace the impact through references"""
        visited: Set[str] = set(symbol_ids)
        impacted_symbols: List[ImpactedSymbol] = []
        file_symbols: Dict[str, List[ImpactedSymbol]] = {}
        
        current_ids = symbol_ids
        distance = 1
        
        while current_ids and distance <= max_depth:
            # Find all references to current symbols
            result = await self.db.execute(
                select(Reference)
                .options(selectinload(Reference.from_symbol).selectinload(Symbol.file))
                .where(
                    Reference.snapshot_id == self.snapshot_id,
                    Reference.to_symbol_id.in_(current_ids),
                )
            )
            references = result.scalars().all()
            
            next_ids = []
            for ref in references:
                if ref.from_symbol and ref.from_symbol_id not in visited:
                    visited.add(ref.from_symbol_id)
                    next_ids.append(ref.from_symbol_id)
                    
                    symbol = ref.from_symbol
                    file_path = symbol.file.path if symbol.file else ""
                    
                    impacted = ImpactedSymbol(
                        id=symbol.id,
                        name=symbol.name,
                        kind=symbol.kind,
                        file_path=file_path,
                        start_line=symbol.start_line,
                        end_line=symbol.end_line,
                        impact_type="direct" if distance == 1 else "transitive",
                        distance=distance,
                    )
                    impacted_symbols.append(impacted)
                    
                    if file_path:
                        if file_path not in file_symbols:
                            file_symbols[file_path] = []
                        file_symbols[file_path].append(impacted)
            
            current_ids = next_ids
            distance += 1
        
        # Build impacted files list
        impacted_files = []
        for path, symbols in file_symbols.items():
            # Get file info
            result = await self.db.execute(
                select(File)
                .where(
                    File.snapshot_id == self.snapshot_id,
                    File.path == path,
                )
            )
            file = result.scalar_one_or_none()
            
            impacted_files.append(ImpactedFile(
                path=path,
                language=file.language if file else None,
                symbols_affected=symbols,
                is_directly_changed=False,
            ))
        
        return impacted_symbols, impacted_files
    
    def _calculate_risk(
        self,
        changed_files: int,
        changed_symbols: int,
        impacted_files: int,
        impacted_symbols: int,
    ) -> tuple[str, str]:
        """Calculate risk level based on impact scope"""
        total_affected = impacted_files + impacted_symbols
        
        if total_affected == 0:
            return "low", "No external dependencies found. Changes are isolated."
        
        if impacted_files <= 2 and impacted_symbols <= 5:
            return "low", f"Limited impact: {impacted_files} file(s) and {impacted_symbols} symbol(s) reference the changes."
        
        if impacted_files <= 5 and impacted_symbols <= 15:
            return "medium", f"Moderate impact: {impacted_files} file(s) and {impacted_symbols} symbol(s) may be affected. Review recommended."
        
        if impacted_files <= 10 and impacted_symbols <= 30:
            return "high", f"Significant impact: {impacted_files} file(s) and {impacted_symbols} symbol(s) depend on these changes. Thorough testing required."
        
        return "critical", f"Critical impact: {impacted_files} file(s) and {impacted_symbols} symbol(s) are affected. This is a core component."
