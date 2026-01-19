"""
File model - represents a file in a snapshot
"""

from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Integer, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.snapshot import Snapshot
    from app.models.symbol import Symbol


class File(Base, TimestampMixin):
    __tablename__ = "files"

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
    
    # File path relative to project root
    path: Mapped[str] = mapped_column(String(1024), nullable=False, index=True)
    
    # File metadata
    language: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    line_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Content hash for change detection
    sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    
    # Flags
    is_binary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Cached content (for small files, optional)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    snapshot: Mapped["Snapshot"] = relationship("Snapshot", back_populates="files")
    symbols: Mapped[List["Symbol"]] = relationship(
        "Symbol",
        back_populates="file",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<File {self.path}>"
    
    @property
    def extension(self) -> Optional[str]:
        """Get file extension"""
        if "." in self.path:
            return self.path.rsplit(".", 1)[-1].lower()
        return None
    
    @property
    def filename(self) -> str:
        """Get filename without path"""
        return self.path.rsplit("/", 1)[-1] if "/" in self.path else self.path
