"""
Architecture Service - Aggregates raw data for auto-generated architecture summaries

Layer 1 of Auto Architecture Summary: collects data from the snapshot to feed:
- System design overview
- Backend–frontend interaction
- Folder responsibility breakdown
- Database schema summary
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from pathlib import Path
from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.file import File
from app.models.symbol import Symbol, SymbolKind
from app.models.snapshot import Snapshot


# Path patterns that suggest backend/API code
BACKEND_PATTERNS = (
    "api", "routes", "app", "backend", "server", "controllers",
    "views", "handlers", "services", "middleware", "main.py", "app.py"
)
# Path patterns that suggest frontend/client code
FRONTEND_PATTERNS = (
    "src", "frontend", "client", "components", "pages", "views",
    "public", "static", "assets", "app.tsx", "main.tsx", "index.tsx"
)
# Path patterns that suggest entry points
ENTRY_PATTERNS = (
    "main.py", "app.py", "index.py", "main.ts", "main.tsx",
    "index.ts", "index.tsx", "app.tsx", "__main__.py"
)
# Path patterns that suggest database models
MODEL_PATTERNS = (
    "models", "model", "schema", "entities", "db"
)
# File extensions for schema definitions
SCHEMA_EXTENSIONS = (".sql", ".prisma", ".gql", ".graphql")


@dataclass
class SystemOverview:
    """High-level system structure"""
    top_folders: List[str]
    file_count: int
    total_lines: int
    languages: Dict[str, int]
    entry_points: List[str]
    tech_hints: List[str]


@dataclass
class FolderBreakdown:
    """Per-folder responsibility"""
    path: str
    name: str
    file_count: int
    total_lines: int
    languages: Dict[str, int]
    purpose: str  # Inferred from path + contents
    key_files: List[str]
    depth: int


@dataclass
class BackendFrontendBoundary:
    """Backend–frontend interaction boundaries"""
    api_paths: List[str]
    client_paths: List[str]
    boundary_files: List[str]
    api_file_count: int
    client_file_count: int


@dataclass
class TableSchema:
    """Inferred database table"""
    name: str
    columns: List[str]
    relationships: List[str]
    source_file: str


@dataclass
class ArchitectureData:
    """Complete raw architecture data for a snapshot"""
    system_overview: SystemOverview
    folder_breakdown: List[FolderBreakdown]
    backend_frontend: BackendFrontendBoundary
    database_schema: List[TableSchema]


def _path_matches(path: str, patterns: tuple) -> bool:
    """Check if path (lowercase) contains any of the patterns"""
    lower = path.lower().replace("\\", "/")
    return any(p in lower for p in patterns)


def _infer_folder_purpose(path: str, languages: Dict[str, int], key_files: List[str]) -> str:
    """Infer folder purpose from path, languages, and key files"""
    lower = path.lower()
    if not path:
        return "Project root"
    if "api" in lower or "routes" in lower or "controllers" in lower:
        return "API / request handling"
    if "models" in lower or "schema" in lower or "db" in lower:
        return "Data models / schema"
    if "components" in lower or "ui" in lower:
        return "UI components"
    if "pages" in lower or "views" in lower:
        return "Pages / views"
    if "services" in lower:
        return "Business logic / services"
    if "utils" in lower or "lib" in lower or "helpers" in lower:
        return "Utilities / helpers"
    if "tests" in lower or "test" in lower:
        return "Tests"
    if "static" in lower or "assets" in lower or "public" in lower:
        return "Static assets"
    if "config" in lower or "settings" in lower:
        return "Configuration"
    if "migrations" in lower:
        return "Database migrations"
    if "frontend" in lower or "client" in lower or "src" in lower:
        return "Frontend / client code"
    if "backend" in lower or "server" in lower:
        return "Backend / server code"
    return "Application code"


class ArchitectureService:
    """Aggregates architecture data from a snapshot"""

    def __init__(self, db: AsyncSession, snapshot_id: str):
        self.db = db
        self.snapshot_id = snapshot_id

    async def _get_files(self) -> List[File]:
        """Load all files for the snapshot"""
        result = await self.db.execute(
            select(File).where(File.snapshot_id == self.snapshot_id)
        )
        return list(result.scalars().all())

    async def _get_symbols(self) -> List[Symbol]:
        """Load all symbols for the snapshot"""
        result = await self.db.execute(
            select(Symbol).where(Symbol.snapshot_id == self.snapshot_id)
        )
        return list(result.scalars().all())

    async def aggregate_system_overview(self, files: List[File]) -> SystemOverview:
        """Build system design overview"""
        top_folders = set()
        languages: Dict[str, int] = defaultdict(int)
        entry_points: List[str] = []
        total_lines = 0

        for f in files:
            path = f.path.replace("\\", "/")
            parts = path.split("/")
            if len(parts) > 1:
                top_folders.add(parts[0])
            elif len(parts) == 1 and path:
                top_folders.add("(root)")

            if f.language:
                languages[f.language] += 1

            total_lines += f.line_count or 0

            if _path_matches(f.filename, ENTRY_PATTERNS):
                entry_points.append(f.path)

        # Tech hints from languages
        tech_hints = []
        if "python" in [l.lower() for l in languages]:
            tech_hints.append("Python")
        if "typescript" in [l.lower() for l in languages]:
            tech_hints.append("TypeScript")
        if "javascript" in [l.lower() for l in languages]:
            tech_hints.append("JavaScript")
        if "vue" in [l.lower() for l in languages]:
            tech_hints.append("Vue")
        if any("react" in l.lower() for l in languages):
            tech_hints.append("React")
        if "sql" in [l.lower() for l in languages]:
            tech_hints.append("SQL")

        return SystemOverview(
            top_folders=sorted(top_folders),
            file_count=len(files),
            total_lines=total_lines,
            languages=dict(languages),
            entry_points=sorted(entry_points),
            tech_hints=tech_hints,
        )

    async def aggregate_folder_breakdown(self, files: List[File]) -> List[FolderBreakdown]:
        """Build folder responsibility breakdown"""
        # Group files by folder
        folder_files: Dict[str, List[File]] = defaultdict(list)
        for f in files:
            path = f.path.replace("\\", "/")
            parent = str(Path(path).parent)
            if parent == ".":
                parent = ""
            folder_files[parent].append(f)

        # Also ensure we have parent folders
        all_folders = set(folder_files.keys())
        for folder in list(all_folders):
            parts = folder.split("/") if folder else []
            for i in range(1, len(parts) + 1):
                parent = "/".join(parts[:i])
                if parent not in folder_files:
                    folder_files[parent] = []

        breakdown: List[FolderBreakdown] = []

        for folder_path in sorted(folder_files.keys(), key=lambda p: (p.count("/"), p)):
            folder_file_list = folder_files[folder_path]
            file_count = len([f for f in folder_file_list if Path(f.path).name])
            total_lines = sum(f.line_count or 0 for f in folder_file_list)
            languages: Dict[str, int] = defaultdict(int)
            for f in folder_file_list:
                if f.language:
                    languages[f.language] += 1

            # Key files: entry points, main modules, or most lines
            key_files = []
            for f in folder_file_list:
                if _path_matches(f.filename, ENTRY_PATTERNS):
                    key_files.append(f.path)
            if not key_files and folder_file_list:
                sorted_by_lines = sorted(
                    folder_file_list,
                    key=lambda x: (x.line_count or 0),
                    reverse=True,
                )[:5]
                key_files = [f.path for f in sorted_by_lines]

            name = Path(folder_path).name if folder_path else "(root)"
            purpose = _infer_folder_purpose(
                folder_path,
                dict(languages),
                key_files,
            )

            breakdown.append(FolderBreakdown(
                path=folder_path,
                name=name,
                file_count=file_count,
                total_lines=total_lines,
                languages=dict(languages),
                purpose=purpose,
                key_files=key_files[:10],
                depth=folder_path.count("/") if folder_path else 0,
            ))

        return breakdown

    async def aggregate_backend_frontend(self, files: List[File]) -> BackendFrontendBoundary:
        """Build backend–frontend boundary analysis"""
        api_paths: List[str] = []
        client_paths: List[str] = []
        boundary_files: List[str] = []

        for f in files:
            path = f.path.replace("\\", "/")
            if _path_matches(path, BACKEND_PATTERNS):
                api_paths.append(path)
            if _path_matches(path, FRONTEND_PATTERNS):
                client_paths.append(path)
            if _path_matches(path, BACKEND_PATTERNS) and _path_matches(path, ("api", "routes")):
                boundary_files.append(path)

        return BackendFrontendBoundary(
            api_paths=sorted(api_paths)[:100],
            client_paths=sorted(client_paths)[:100],
            boundary_files=sorted(boundary_files)[:50],
            api_file_count=len(api_paths),
            client_file_count=len(client_paths),
        )

    async def aggregate_database_schema(
        self,
        files: List[File],
        symbols: List[Symbol],
    ) -> List[TableSchema]:
        """Infer database schema from model files and symbols"""
        file_map = {f.id: f for f in files}
        tables: List[TableSchema] = []

        # Find model files
        model_files = [
            f for f in files
            if _path_matches(f.path, MODEL_PATTERNS)
            or f.path.lower().endswith(SCHEMA_EXTENSIONS)
        ]

        # Get classes from model files (potential tables)
        for f in model_files:
            file_symbols = [s for s in symbols if s.file_id == f.id]
            classes = [s for s in file_symbols if s.kind == SymbolKind.CLASS]

            for cls in classes:
                # Heuristic: class name often matches table name (PascalCase -> snake_case)
                name = cls.name
                columns = []
                relationships = []

                # Look for child symbols (attributes, methods) as column hints
                for s in file_symbols:
                    if s.parent_id == cls.id:
                        if s.kind in (SymbolKind.PROPERTY, SymbolKind.VARIABLE, SymbolKind.CONSTANT):
                            columns.append(s.name)
                        elif s.kind == SymbolKind.METHOD and "relationship" in (s.signature or "").lower():
                            relationships.append(s.name)

                tables.append(TableSchema(
                    name=name,
                    columns=columns or ["(inferred from model)"],
                    relationships=relationships,
                    source_file=f.path,
                ))

        # Deduplicate by name
        seen = set()
        unique_tables = []
        for t in tables:
            if t.name not in seen:
                seen.add(t.name)
                unique_tables.append(t)

        return unique_tables

    async def aggregate(self) -> ArchitectureData:
        """Aggregate all architecture data for the snapshot"""
        files = await self._get_files()
        symbols = await self._get_symbols()

        system_overview = await self.aggregate_system_overview(files)
        folder_breakdown = await self.aggregate_folder_breakdown(files)
        backend_frontend = await self.aggregate_backend_frontend(files)
        database_schema = await self.aggregate_database_schema(files, symbols)

        return ArchitectureData(
            system_overview=system_overview,
            folder_breakdown=folder_breakdown,
            backend_frontend=backend_frontend,
            database_schema=database_schema,
        )

    def to_dict(self, data: ArchitectureData) -> Dict[str, Any]:
        """Convert ArchitectureData to JSON-serializable dict"""
        return {
            "system_overview": {
                "top_folders": data.system_overview.top_folders,
                "file_count": data.system_overview.file_count,
                "total_lines": data.system_overview.total_lines,
                "languages": data.system_overview.languages,
                "entry_points": data.system_overview.entry_points,
                "tech_hints": data.system_overview.tech_hints,
            },
            "folder_breakdown": [
                {
                    "path": fb.path,
                    "name": fb.name,
                    "file_count": fb.file_count,
                    "total_lines": fb.total_lines,
                    "languages": fb.languages,
                    "purpose": fb.purpose,
                    "key_files": fb.key_files,
                    "depth": fb.depth,
                }
                for fb in data.folder_breakdown
            ],
            "backend_frontend": {
                "api_paths": data.backend_frontend.api_paths,
                "client_paths": data.backend_frontend.client_paths,
                "boundary_files": data.backend_frontend.boundary_files,
                "api_file_count": data.backend_frontend.api_file_count,
                "client_file_count": data.backend_frontend.client_file_count,
            },
            "database_schema": [
                {
                    "name": t.name,
                    "columns": t.columns,
                    "relationships": t.relationships,
                    "source_file": t.source_file,
                }
                for t in data.database_schema
            ],
        }
