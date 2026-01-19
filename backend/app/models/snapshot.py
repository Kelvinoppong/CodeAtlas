"""
Snapshot model - represents an indexed state of a project
"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Integer, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
import enum

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.file import File
    from app.models.symbol import Symbol


class SnapshotStatus(str, enum.Enum):
    PENDING = "pending"
    INDEXING = "indexing"
    READY = "ready"
    FAILED = "failed"


class Snapshot(Base, TimestampMixin):
    __tablename__ = "snapshots"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Git commit this snapshot represents (if applicable)
    git_commit: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    git_branch: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Indexing status
    status: Mapped[SnapshotStatus] = mapped_column(
        SQLEnum(SnapshotStatus),
        default=SnapshotStatus.PENDING,
        nullable=False,
    )
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    
    # Statistics
    file_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    symbol_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_lines: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Index version for compatibility
    index_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="snapshots")
    files: Mapped[List["File"]] = relationship(
        "File",
        back_populates="snapshot",
        cascade="all, delete-orphan",
    )
    symbols: Mapped[List["Symbol"]] = relationship(
        "Symbol",
        back_populates="snapshot",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Snapshot {self.id[:8]} ({self.status.value})>"
