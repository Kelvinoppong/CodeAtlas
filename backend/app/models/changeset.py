"""
ChangeSet and Patch models - for safe AI modifications
"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Text, DateTime, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
import enum

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.snapshot import Snapshot


class ChangeSetStatus(str, enum.Enum):
    PROPOSED = "proposed"
    APPLIED = "applied"
    ROLLED_BACK = "rolled_back"
    REJECTED = "rejected"


class ChangeSet(Base, TimestampMixin):
    __tablename__ = "changesets"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    snapshot_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("snapshots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Description
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status tracking
    status: Mapped[ChangeSetStatus] = mapped_column(
        SQLEnum(ChangeSetStatus),
        default=ChangeSetStatus.PROPOSED,
        nullable=False,
    )
    
    # Timestamps for status changes
    applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rolled_back_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Git commit if created
    git_commit_sha: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    git_commit_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # AI-generated metadata
    ai_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ai_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    patches: Mapped[List["Patch"]] = relationship(
        "Patch",
        back_populates="changeset",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<ChangeSet {self.title[:30]} ({self.status.value})>"


class Patch(Base, TimestampMixin):
    __tablename__ = "patches"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    changeset_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("changesets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Target file
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    
    # Content before and after
    original_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Unified diff format
    diff: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Order of application
    order: Mapped[int] = mapped_column(default=0, nullable=False)
    
    # Relationships
    changeset: Mapped["ChangeSet"] = relationship("ChangeSet", back_populates="patches")

    def __repr__(self) -> str:
        return f"<Patch {self.file_path}>"
