"""
Incremental Indexer - Only re-index changed files
"""

from dataclasses import dataclass
from typing import List, Set, Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.file import File
from app.models.snapshot import Snapshot
from app.indexer.scanner import FileScanner, ScannedFile


@dataclass
class FileChange:
    """Represents a change to a file"""
    path: str
    change_type: str  # "added", "modified", "deleted"
    old_sha256: Optional[str] = None
    new_sha256: Optional[str] = None


@dataclass
class IncrementalDiff:
    """Diff between two snapshots or filesystem state"""
    added_files: List[ScannedFile]
    modified_files: List[ScannedFile]
    deleted_paths: List[str]
    unchanged_count: int
    
    @property
    def total_changes(self) -> int:
        return len(self.added_files) + len(self.modified_files) + len(self.deleted_paths)
    
    @property
    def has_changes(self) -> bool:
        return self.total_changes > 0


class IncrementalIndexer:
    """
    Service for incremental indexing - detects file changes and only
    re-indexes what's necessary.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_file_hashes(self, snapshot_id: str) -> Dict[str, str]:
        """Get all file paths and their SHA256 hashes from a snapshot"""
        result = await self.db.execute(
            select(File.path, File.sha256)
            .where(File.snapshot_id == snapshot_id)
        )
        return {row[0]: row[1] for row in result.all()}
    
    async def compute_diff(
        self,
        project_path: str,
        base_snapshot_id: Optional[str] = None,
    ) -> IncrementalDiff:
        """
        Compute the difference between the current filesystem state
        and a base snapshot.
        
        If base_snapshot_id is None, treats all files as added.
        """
        # Scan current filesystem
        scanner = FileScanner(project_path)
        current_files = scanner.scan_all()
        
        # Create lookup by path
        current_by_path: Dict[str, ScannedFile] = {f.path: f for f in current_files}
        current_paths = set(current_by_path.keys())
        
        if not base_snapshot_id:
            # No base - everything is new
            return IncrementalDiff(
                added_files=current_files,
                modified_files=[],
                deleted_paths=[],
                unchanged_count=0,
            )
        
        # Get base snapshot file hashes
        base_hashes = await self.get_file_hashes(base_snapshot_id)
        base_paths = set(base_hashes.keys())
        
        # Compute differences
        added_paths = current_paths - base_paths
        deleted_paths = base_paths - current_paths
        common_paths = current_paths & base_paths
        
        added_files = [current_by_path[p] for p in added_paths]
        deleted = list(deleted_paths)
        
        # Check for modifications among common files
        modified_files = []
        unchanged_count = 0
        
        for path in common_paths:
            current_file = current_by_path[path]
            base_hash = base_hashes[path]
            
            if current_file.sha256 != base_hash:
                modified_files.append(current_file)
            else:
                unchanged_count += 1
        
        return IncrementalDiff(
            added_files=added_files,
            modified_files=modified_files,
            deleted_paths=deleted,
            unchanged_count=unchanged_count,
        )
    
    async def copy_unchanged_files(
        self,
        source_snapshot_id: str,
        target_snapshot_id: str,
        paths: Set[str],
    ) -> int:
        """
        Copy file records from source snapshot to target snapshot
        for unchanged files (avoiding re-parsing).
        
        Returns the number of files copied.
        """
        if not paths:
            return 0
        
        # Get source files
        result = await self.db.execute(
            select(File)
            .where(
                File.snapshot_id == source_snapshot_id,
                File.path.in_(paths),
            )
        )
        source_files = result.scalars().all()
        
        copied = 0
        for source in source_files:
            # Create new file record for target snapshot
            new_file = File(
                snapshot_id=target_snapshot_id,
                path=source.path,
                language=source.language,
                size_bytes=source.size_bytes,
                line_count=source.line_count,
                sha256=source.sha256,
                is_binary=source.is_binary,
                content=source.content,
            )
            self.db.add(new_file)
            copied += 1
        
        await self.db.flush()
        return copied
    
    async def get_latest_snapshot(self, project_id: str) -> Optional[Snapshot]:
        """Get the latest ready snapshot for a project"""
        from app.models.snapshot import SnapshotStatus
        
        result = await self.db.execute(
            select(Snapshot)
            .where(
                Snapshot.project_id == project_id,
                Snapshot.status == SnapshotStatus.READY,
            )
            .order_by(Snapshot.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    def estimate_time_savings(self, diff: IncrementalDiff, avg_file_time_ms: float = 50) -> Tuple[float, float]:
        """
        Estimate time savings from incremental indexing.
        
        Returns:
            (estimated_time_ms, saved_time_ms)
        """
        total_files = diff.unchanged_count + len(diff.added_files) + len(diff.modified_files)
        files_to_process = len(diff.added_files) + len(diff.modified_files)
        
        full_time = total_files * avg_file_time_ms
        incremental_time = files_to_process * avg_file_time_ms
        saved_time = full_time - incremental_time
        
        return (incremental_time, saved_time)
