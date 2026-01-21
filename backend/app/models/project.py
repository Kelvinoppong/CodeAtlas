"""
Project model - represents an imported repository
"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Text, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.snapshot import Snapshot
    from app.models.user import ProjectMembership


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Path to the project (local filesystem or remote URL)
    root_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    
    # Git information
    git_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    default_branch: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Ownership
    created_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    
    # Visibility: public projects can be viewed by anyone
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Settings stored as JSON
    settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    
    # Relationships
    snapshots: Mapped[List["Snapshot"]] = relationship(
        "Snapshot",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    memberships: Mapped[List["ProjectMembership"]] = relationship(
        "ProjectMembership",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Project {self.name} ({self.id[:8]})>"
