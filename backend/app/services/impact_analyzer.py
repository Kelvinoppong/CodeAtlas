"""
Impact Analyzer - Analyzes what breaks when code changes

Core differentiator feature: "If I modify this function, what breaks?"

This module demonstrates:
- Graph data structures (symbol reference graph)
- BFS/DFS traversal algorithms
- Static analysis thinking
- Risk modeling and scoring
"""

from dataclasses import dataclass, field
from typing import List, Set, Optional, Dict, Tuple
from collections import deque
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.symbol import Symbol, Reference, SymbolKind, ReferenceKind
from app.models.file import File


# Symbol kind weights for risk calculation (higher = more impactful)
SYMBOL_KIND_WEIGHTS: Dict[SymbolKind, float] = {
    SymbolKind.CLASS: 1.0,
    SymbolKind.INTERFACE: 1.0,
    SymbolKind.MODULE: 0.9,
    SymbolKind.FUNCTION: 0.7,
    SymbolKind.METHOD: 0.7,
    SymbolKind.TYPE: 0.6,
    SymbolKind.ENUM: 0.6,
    SymbolKind.PROPERTY: 0.4,
    SymbolKind.VARIABLE: 0.3,
    SymbolKind.CONSTANT: 0.3,
    SymbolKind.IMPORT: 0.2,
}

# Reference kind labels for display
REFERENCE_KIND_LABELS: Dict[ReferenceKind, str] = {
    ReferenceKind.CALL: "calls",
    ReferenceKind.IMPORT: "imports",
    ReferenceKind.USAGE: "uses",
    ReferenceKind.INHERITANCE: "extends",
    ReferenceKind.IMPLEMENTATION: "implements",
    ReferenceKind.TYPE_REFERENCE: "references type",
}


@dataclass
class ImpactPath:
    """Represents the path from a changed symbol to an impacted symbol"""
    symbols: List[str]  # List of symbol IDs in the path
    symbol_names: List[str]  # List of symbol names for display
    reference_kinds: List[str]  # The kind of each reference in the path


@dataclass
class ImpactedSymbol:
    """A symbol that would be affected by a change"""
    id: str
    name: str
    kind: str
    file_path: str
    start_line: int
    end_line: int
    impact_type: str  # "direct" or "transitive"
    distance: int  # How many hops from the changed symbol
    reference_kind: Optional[str] = None  # How this symbol references the changed one
    reference_context: Optional[str] = None  # The line of code where reference occurs
    reference_line: Optional[int] = None  # Line number of the reference
    impact_path: Optional[ImpactPath] = None  # Full path from changed to impacted


@dataclass
class ImpactedFile:
    """A file that contains impacted symbols"""
    path: str
    language: Optional[str]
    symbols_affected: List[ImpactedSymbol] = field(default_factory=list)
    is_directly_changed: bool = False
    direct_impact_count: int = 0
    transitive_impact_count: int = 0


@dataclass
class ImpactGraphNode:
    """Node in the impact visualization graph"""
    id: str
    name: str
    kind: str
    file_path: str
    line: int
    node_type: str  # "changed", "direct", "transitive"
    distance: int


@dataclass
class ImpactGraphEdge:
    """Edge in the impact visualization graph"""
    source: str  # Symbol ID
    target: str  # Symbol ID
    kind: str  # Reference kind
    label: str  # Human-readable label
    context: Optional[str] = None  # The line of code


@dataclass
class ImpactGraph:
    """Graph data for visualization"""
    nodes: List[ImpactGraphNode] = field(default_factory=list)
    edges: List[ImpactGraphEdge] = field(default_factory=list)


@dataclass
class ImpactAnalysis:
    """Complete impact analysis result"""
    changed_files: List[str]
    changed_symbols: List[ImpactedSymbol]
    impacted_files: List[ImpactedFile]
    impacted_symbols: List[ImpactedSymbol]
    total_files_affected: int
    total_symbols_affected: int
    risk_level: str  # "low", "medium", "high", "critical"
    risk_score: float  # 0.0 to 1.0
    risk_explanation: str
    impact_graph: ImpactGraph = field(default_factory=ImpactGraph)
    circular_dependencies: List[List[str]] = field(default_factory=list)  # Detected cycles


class ImpactAnalyzer:
    """
    Analyzes the impact of code changes across the codebase.
    
    Uses BFS traversal to find all symbols that reference (directly or transitively)
    the changed symbols, providing:
    - Risk scoring based on impact scope and symbol importance
    - Path tracking to show how changes propagate
    - Graph data for visualization
    - Circular dependency detection
    """
    
    def __init__(self, db: AsyncSession, snapshot_id: str):
        self.db = db
        self.snapshot_id = snapshot_id
    
    async def analyze_file_changes(
        self, 
        file_paths: List[str],
        max_depth: int = 3
    ) -> ImpactAnalysis:
        """
        Analyze the impact of changing specified files.
        
        Args:
            file_paths: List of file paths being changed
            max_depth: Maximum depth for transitive impact analysis
            
        Returns:
            Complete ImpactAnalysis result
        """
        # Get all symbols in the changed files
        result = await self.db.execute(
            select(Symbol)
            .options(selectinload(Symbol.file))
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
                kind=s.kind.value if isinstance(s.kind, SymbolKind) else s.kind,
                file_path=s.file.path if s.file else "",
                start_line=s.start_line,
                end_line=s.end_line,
                impact_type="changed",
                distance=0,
            )
            for s in changed_symbols
        ]
        
        # Find all references to these symbols with path tracking
        symbol_ids = [s.id for s in changed_symbols]
        impact_result = await self._trace_impact_with_paths(
            symbol_ids,
            {s.id: s.name for s in changed_symbols},
            max_depth
        )
        
        impacted_symbols = impact_result["symbols"]
        impacted_files = impact_result["files"]
        impact_graph = impact_result["graph"]
        cycles = impact_result["cycles"]
        
        # Calculate risk level with weighted scoring
        risk_level, risk_score, risk_explanation = self._calculate_weighted_risk(
            changed_files=len(file_paths),
            changed_symbols=changed_symbols,
            impacted_files=len(impacted_files),
            impacted_symbols=impacted_symbols,
        )
        
        return ImpactAnalysis(
            changed_files=file_paths,
            changed_symbols=changed_symbol_data,
            impacted_files=impacted_files,
            impacted_symbols=impacted_symbols,
            total_files_affected=len(impacted_files) + len(file_paths),
            total_symbols_affected=len(impacted_symbols) + len(changed_symbols),
            risk_level=risk_level,
            risk_score=risk_score,
            risk_explanation=risk_explanation,
            impact_graph=impact_graph,
            circular_dependencies=cycles,
        )
    
    async def analyze_symbol_changes(
        self, 
        symbol_ids: List[str],
        max_depth: int = 3
    ) -> ImpactAnalysis:
        """
        Analyze the impact of changing specified symbols.
        
        Args:
            symbol_ids: List of symbol IDs being changed
            max_depth: Maximum depth for transitive impact analysis
            
        Returns:
            Complete ImpactAnalysis result
        """
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
                kind=s.kind.value if isinstance(s.kind, SymbolKind) else s.kind,
                file_path=s.file.path if s.file else "",
                start_line=s.start_line,
                end_line=s.end_line,
                impact_type="changed",
                distance=0,
            )
            for s in symbols
        ]
        
        # Trace impact with paths
        symbol_names = {s.id: s.name for s in symbols}
        impact_result = await self._trace_impact_with_paths(
            symbol_ids,
            symbol_names,
            max_depth
        )
        
        impacted_symbols = impact_result["symbols"]
        impacted_files = impact_result["files"]
        impact_graph = impact_result["graph"]
        cycles = impact_result["cycles"]
        
        # Calculate risk
        risk_level, risk_score, risk_explanation = self._calculate_weighted_risk(
            changed_files=len(changed_files),
            changed_symbols=symbols,
            impacted_files=len(impacted_files),
            impacted_symbols=impacted_symbols,
        )
        
        return ImpactAnalysis(
            changed_files=changed_files,
            changed_symbols=changed_symbol_data,
            impacted_files=impacted_files,
            impacted_symbols=impacted_symbols,
            total_files_affected=len(impacted_files) + len(changed_files),
            total_symbols_affected=len(impacted_symbols) + len(symbols),
            risk_level=risk_level,
            risk_score=risk_score,
            risk_explanation=risk_explanation,
            impact_graph=impact_graph,
            circular_dependencies=cycles,
        )
    
    async def _trace_impact_with_paths(
        self,
        start_symbol_ids: List[str],
        start_symbol_names: Dict[str, str],
        max_depth: int = 3
    ) -> Dict:
        """
        Trace impact through references using BFS with path tracking.
        
        Uses a breadth-first search to find all symbols that reference
        the changed symbols, tracking the full path of references.
        
        Args:
            start_symbol_ids: IDs of the symbols being changed
            start_symbol_names: Mapping of symbol ID to name for path display
            max_depth: Maximum traversal depth
            
        Returns:
            Dictionary with keys: symbols, files, graph, cycles
        """
        visited: Set[str] = set(start_symbol_ids)
        impacted_symbols: List[ImpactedSymbol] = []
        file_symbols: Dict[str, List[ImpactedSymbol]] = {}
        
        # For cycle detection
        cycles: List[List[str]] = []
        
        # Build graph for visualization
        graph = ImpactGraph()
        
        # Add changed symbols as root nodes
        for sym_id in start_symbol_ids:
            graph.nodes.append(ImpactGraphNode(
                id=sym_id,
                name=start_symbol_names.get(sym_id, "unknown"),
                kind="unknown",  # Will be updated if we have the data
                file_path="",
                line=0,
                node_type="changed",
                distance=0,
            ))
        
        # Track paths: symbol_id -> (parent_id, reference_kind)
        parent_map: Dict[str, Tuple[str, str, str]] = {}  # id -> (parent_id, ref_kind, ref_context)
        
        # BFS queue: (symbol_id, distance, path_so_far)
        queue: deque = deque()
        for sym_id in start_symbol_ids:
            queue.append((sym_id, 0, [sym_id]))
        
        while queue:
            current_id, distance, current_path = queue.popleft()
            
            if distance >= max_depth:
                continue
            
            # Find all references TO this symbol (who depends on it)
            result = await self.db.execute(
                select(Reference)
                .options(
                    selectinload(Reference.from_symbol).selectinload(Symbol.file)
                )
                .where(
                    Reference.snapshot_id == self.snapshot_id,
                    Reference.to_symbol_id == current_id,
                )
            )
            references = result.scalars().all()
            
            for ref in references:
                if not ref.from_symbol:
                    continue
                    
                from_sym_id = ref.from_symbol_id
                
                # Cycle detection
                if from_sym_id in current_path:
                    cycle = current_path[current_path.index(from_sym_id):] + [from_sym_id]
                    cycles.append(cycle)
                    continue
                
                if from_sym_id in visited:
                    continue
                    
                visited.add(from_sym_id)
                
                symbol = ref.from_symbol
                file_path = symbol.file.path if symbol.file else ""
                ref_kind = ref.kind.value if isinstance(ref.kind, ReferenceKind) else str(ref.kind)
                ref_label = REFERENCE_KIND_LABELS.get(ref.kind, ref_kind)
                
                # Build the impact path
                path_symbol_ids = current_path + [from_sym_id]
                path_symbol_names = [
                    start_symbol_names.get(sid, "?") for sid in path_symbol_ids[:-1]
                ] + [symbol.name]
                
                impact_path = ImpactPath(
                    symbols=path_symbol_ids,
                    symbol_names=path_symbol_names,
                    reference_kinds=[ref_label] * (len(path_symbol_ids) - 1)
                )
                
                impacted = ImpactedSymbol(
                    id=symbol.id,
                    name=symbol.name,
                    kind=symbol.kind.value if isinstance(symbol.kind, SymbolKind) else symbol.kind,
                    file_path=file_path,
                    start_line=symbol.start_line,
                    end_line=symbol.end_line,
                    impact_type="direct" if distance == 0 else "transitive",
                    distance=distance + 1,
                    reference_kind=ref_kind,
                    reference_context=getattr(ref, 'context', None),
                    reference_line=ref.line,
                    impact_path=impact_path,
                )
                impacted_symbols.append(impacted)
                
                # Add to graph
                graph.nodes.append(ImpactGraphNode(
                    id=symbol.id,
                    name=symbol.name,
                    kind=impacted.kind,
                    file_path=file_path,
                    line=symbol.start_line,
                    node_type="direct" if distance == 0 else "transitive",
                    distance=distance + 1,
                ))
                
                graph.edges.append(ImpactGraphEdge(
                    source=from_sym_id,  # The impacted symbol
                    target=current_id,   # The symbol it references
                    kind=ref_kind,
                    label=ref_label,
                    context=getattr(ref, 'context', None),
                ))
                
                # Track by file
                if file_path:
                    if file_path not in file_symbols:
                        file_symbols[file_path] = []
                    file_symbols[file_path].append(impacted)
                
                # Add to queue for further traversal
                new_path = current_path + [from_sym_id]
                queue.append((from_sym_id, distance + 1, new_path))
        
        # Build impacted files list
        impacted_files: List[ImpactedFile] = []
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
            
            direct_count = sum(1 for s in symbols if s.impact_type == "direct")
            transitive_count = sum(1 for s in symbols if s.impact_type == "transitive")
            
            impacted_files.append(ImpactedFile(
                path=path,
                language=file.language if file else None,
                symbols_affected=symbols,
                is_directly_changed=False,
                direct_impact_count=direct_count,
                transitive_impact_count=transitive_count,
            ))
        
        # Sort by impact severity (direct first, then by count)
        impacted_files.sort(key=lambda f: (-f.direct_impact_count, -f.transitive_impact_count))
        
        return {
            "symbols": impacted_symbols,
            "files": impacted_files,
            "graph": graph,
            "cycles": cycles,
        }
    
    def _calculate_weighted_risk(
        self,
        changed_files: int,
        changed_symbols: List[Symbol],
        impacted_files: int,
        impacted_symbols: List[ImpactedSymbol],
    ) -> Tuple[str, float, str]:
        """
        Calculate risk level with weighted scoring based on symbol importance.
        
        Factors:
        - Number of files affected (weight: 0.3)
        - Number of symbols affected (weight: 0.2)
        - Symbol kind weights (weight: 0.3)
        - Maximum depth of impact (weight: 0.2)
        
        Returns:
            Tuple of (risk_level, risk_score, explanation)
        """
        if not impacted_symbols and not impacted_files:
            return "low", 0.0, "No external dependencies found. Changes are isolated."
        
        # Calculate base metrics
        file_score = min(impacted_files / 20, 1.0)  # Cap at 20 files
        symbol_count = len(impacted_symbols)
        symbol_score = min(symbol_count / 50, 1.0)  # Cap at 50 symbols
        
        # Calculate weighted symbol importance
        total_weight = 0.0
        for sym in impacted_symbols:
            try:
                kind = SymbolKind(sym.kind)
                total_weight += SYMBOL_KIND_WEIGHTS.get(kind, 0.5)
            except ValueError:
                total_weight += 0.5  # Default weight for unknown kinds
        
        avg_weight = total_weight / max(len(impacted_symbols), 1)
        importance_score = avg_weight
        
        # Calculate depth score (deeper = higher risk)
        max_depth = max((s.distance for s in impacted_symbols), default=0)
        depth_score = min(max_depth / 5, 1.0)  # Cap at depth 5
        
        # Weight the scores
        risk_score = (
            file_score * 0.3 +
            symbol_score * 0.2 +
            importance_score * 0.3 +
            depth_score * 0.2
        )
        
        # Determine risk level
        if risk_score < 0.25:
            level = "low"
        elif risk_score < 0.50:
            level = "medium"
        elif risk_score < 0.75:
            level = "high"
        else:
            level = "critical"
        
        # Build explanation
        explanations = []
        
        if impacted_files == 0:
            explanations.append("No files affected")
        elif impacted_files <= 2:
            explanations.append(f"{impacted_files} file(s) may be affected")
        else:
            explanations.append(f"{impacted_files} files contain dependencies")
        
        if symbol_count > 0:
            direct_count = sum(1 for s in impacted_symbols if s.impact_type == "direct")
            transitive_count = symbol_count - direct_count
            
            parts = []
            if direct_count > 0:
                parts.append(f"{direct_count} direct")
            if transitive_count > 0:
                parts.append(f"{transitive_count} transitive")
            
            explanations.append(f"{symbol_count} symbols ({', '.join(parts)})")
        
        if max_depth > 2:
            explanations.append(f"impact propagates {max_depth} levels deep")
        
        # Add high-importance symbols warning
        high_impact_kinds = [SymbolKind.CLASS, SymbolKind.INTERFACE, SymbolKind.MODULE]
        critical_symbols = [
            s for s in impacted_symbols
            if s.kind in [k.value for k in high_impact_kinds]
        ]
        if critical_symbols:
            explanations.append(f"includes {len(critical_symbols)} class/interface/module dependencies")
        
        explanation = ". ".join(explanations) + "."
        
        return level, round(risk_score, 2), explanation
    
    # Keep the old method for backwards compatibility
    async def _trace_impact(
        self,
        symbol_ids: List[str],
        max_depth: int = 3
    ) -> Tuple[List[ImpactedSymbol], List[ImpactedFile]]:
        """Legacy method for backwards compatibility"""
        result = await self._trace_impact_with_paths(
            symbol_ids,
            {},
            max_depth
        )
        return result["symbols"], result["files"]
    
    def _calculate_risk(
        self,
        changed_files: int,
        changed_symbols: int,
        impacted_files: int,
        impacted_symbols: int,
    ) -> Tuple[str, str]:
        """Legacy method for backwards compatibility"""
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
