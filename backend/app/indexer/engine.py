"""
Indexing Engine - orchestrates the full indexing pipeline
"""

import asyncio
from typing import Optional, Callable, Any
from datetime import datetime
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.project import Project
from app.models.snapshot import Snapshot, SnapshotStatus
from app.models.file import File
from app.models.symbol import Symbol, SymbolKind
from app.indexer.scanner import FileScanner, ScannedFile
from app.indexer.parser import CodeParser, ExtractedSymbol


class IndexingEngine:
    """Orchestrates the indexing of a project"""

    def __init__(
        self,
        db: AsyncSession,
        progress_callback: Optional[Callable[[float, str], Any]] = None,
    ):
        self.db = db
        self.progress_callback = progress_callback
        self.parser = CodeParser()

    async def _report_progress(self, progress: float, message: str) -> None:
        """Report indexing progress"""
        if self.progress_callback:
            if asyncio.iscoroutinefunction(self.progress_callback):
                await self.progress_callback(progress, message)
            else:
                self.progress_callback(progress, message)

    async def index_project(
        self,
        project_id: str,
        git_commit: Optional[str] = None,
    ) -> Snapshot:
        """
        Index a project and create a new snapshot.

        Args:
            project_id: The project to index
            git_commit: Optional git commit hash

        Returns:
            The created Snapshot
        """
        # Get project
        result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()

        if not project:
            raise ValueError(f"Project {project_id} not found")

        if not project.root_path:
            raise ValueError(f"Project {project_id} has no root path")

        root_path = Path(project.root_path)
        if not root_path.exists():
            raise ValueError(f"Project path does not exist: {root_path}")

        # Create snapshot
        snapshot = Snapshot(
            project_id=project_id,
            git_commit=git_commit,
            status=SnapshotStatus.INDEXING,
            progress=0.0,
        )
        self.db.add(snapshot)
        await self.db.flush()

        await self._report_progress(5, "Scanning files...")

        try:
            # Scan files
            scanner = FileScanner(str(root_path))
            scanned_files = scanner.scan_all()

            total_files = len(scanned_files)
            await self._report_progress(10, f"Found {total_files} files")

            # Process files
            file_count = 0
            symbol_count = 0
            total_lines = 0

            for i, scanned in enumerate(scanned_files):
                progress = 10 + (i / total_files) * 80  # 10-90%
                await self._report_progress(progress, f"Processing {scanned.path}")

                # Create file record
                file_record = File(
                    snapshot_id=snapshot.id,
                    path=scanned.path,
                    language=scanned.language,
                    size_bytes=scanned.size_bytes,
                    line_count=scanned.line_count,
                    sha256=scanned.sha256,
                    is_binary=scanned.is_binary,
                    content=scanned.content if scanned.size_bytes < 100000 else None,  # Only cache small files
                )
                self.db.add(file_record)
                await self.db.flush()

                file_count += 1
                total_lines += scanned.line_count

                # Parse symbols if we have content and language
                if scanned.content and scanned.language:
                    parse_result = self.parser.parse(scanned.content, scanned.language)

                    # Store symbol -> id mapping for parent references
                    symbol_map = {}

                    for extracted in parse_result.symbols:
                        symbol = Symbol(
                            snapshot_id=snapshot.id,
                            file_id=file_record.id,
                            name=extracted.name,
                            kind=SymbolKind(extracted.kind.value),
                            start_line=extracted.start_line,
                            end_line=extracted.end_line,
                            start_col=extracted.start_col,
                            end_col=extracted.end_col,
                            signature=extracted.signature,
                            docstring=extracted.docstring,
                        )
                        self.db.add(symbol)
                        await self.db.flush()

                        symbol_map[extracted.name] = symbol.id
                        symbol_count += 1

                        # Link to parent if exists
                        if extracted.parent_name and extracted.parent_name in symbol_map:
                            symbol.parent_id = symbol_map[extracted.parent_name]

                # Commit in batches
                if i % 50 == 0:
                    await self.db.commit()

            # Finalize snapshot
            snapshot.status = SnapshotStatus.READY
            snapshot.progress = 100.0
            snapshot.file_count = file_count
            snapshot.symbol_count = symbol_count
            snapshot.total_lines = total_lines

            await self.db.commit()
            await self._report_progress(100, "Indexing complete!")

            return snapshot

        except Exception as e:
            snapshot.status = SnapshotStatus.FAILED
            snapshot.error_message = str(e)[:1000]
            await self.db.commit()
            raise

    async def build_file_tree(self, snapshot_id: str) -> dict:
        """Build file tree structure from indexed files"""
        result = await self.db.execute(
            select(File).where(File.snapshot_id == snapshot_id)
        )
        files = result.scalars().all()

        # Build tree structure
        tree = {"name": "root", "path": "", "type": "folder", "children": []}
        path_to_node = {"": tree}

        for file in files:
            parts = Path(file.path).parts
            current_path = ""

            # Create folder nodes
            for part in parts[:-1]:
                parent_path = current_path
                current_path = str(Path(current_path) / part) if current_path else part

                if current_path not in path_to_node:
                    folder_node = {
                        "name": part,
                        "path": current_path,
                        "type": "folder",
                        "children": [],
                    }
                    path_to_node[parent_path]["children"].append(folder_node)
                    path_to_node[current_path] = folder_node

            # Add file node
            parent_path = str(Path(file.path).parent)
            if parent_path == ".":
                parent_path = ""

            file_node = {
                "name": parts[-1] if parts else file.path,
                "path": file.path,
                "type": "file",
                "language": file.language,
                "size": file.size_bytes,
            }

            if parent_path in path_to_node:
                path_to_node[parent_path]["children"].append(file_node)
            else:
                tree["children"].append(file_node)

        # Sort children
        def sort_children(node: dict) -> None:
            if "children" in node:
                node["children"].sort(
                    key=lambda x: (0 if x["type"] == "folder" else 1, x["name"].lower())
                )
                for child in node["children"]:
                    sort_children(child)

        sort_children(tree)
        return tree

    async def get_dependency_graph(
        self,
        snapshot_id: str,
        file_path: Optional[str] = None,
    ) -> dict:
        """Build dependency graph for visualization"""
        # Get all files
        query = select(File).where(File.snapshot_id == snapshot_id)
        result = await self.db.execute(query)
        files = result.scalars().all()

        # Get all symbols
        query = select(Symbol).where(Symbol.snapshot_id == snapshot_id)
        result = await self.db.execute(query)
        symbols = result.scalars().all()

        nodes = []
        edges = []
        file_map = {f.id: f for f in files}

        # Add file nodes
        for file in files:
            if file_path and file.path != file_path:
                continue

            nodes.append({
                "id": f"file:{file.id}",
                "label": file.filename,
                "type": "file",
                "path": file.path,
                "language": file.language,
            })

        # Add symbol nodes and edges
        for symbol in symbols:
            if symbol.file_id not in file_map:
                continue

            file = file_map[symbol.file_id]
            if file_path and file.path != file_path:
                continue

            nodes.append({
                "id": f"symbol:{symbol.id}",
                "label": symbol.name,
                "type": symbol.kind.value,
                "file": file.path,
                "line": symbol.start_line,
            })

            # Edge from file to symbol
            edges.append({
                "source": f"file:{file.id}",
                "target": f"symbol:{symbol.id}",
                "type": "contains",
            })

            # Edge from parent to child
            if symbol.parent_id:
                edges.append({
                    "source": f"symbol:{symbol.parent_id}",
                    "target": f"symbol:{symbol.id}",
                    "type": "parent",
                })

        return {"nodes": nodes, "edges": edges}
