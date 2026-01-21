"""
User model - authentication and identity
"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.audit import AuditLog


class User(Base, TimestampMixin):
    """User account for authentication and authorization"""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    
    # Authentication
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Profile
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Timestamps
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    memberships: Mapped[List["ProjectMembership"]] = relationship(
        "ProjectMembership",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"


class ProjectMembership(Base, TimestampMixin):
    """User membership in a project with role"""
    __tablename__ = "project_memberships"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    
    user_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
    )
    project_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
    )
    
    # Role: owner, admin, editor, viewer
    role: Mapped[str] = mapped_column(String(50), default="viewer", nullable=False)
    
    # Invitation tracking
    invited_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="memberships")
    project: Mapped["Project"] = relationship("Project", back_populates="memberships")

    def __repr__(self) -> str:
        return f"<ProjectMembership user={self.user_id} project={self.project_id} role={self.role}>"


# Role permissions mapping
ROLE_PERMISSIONS = {
    "owner": {
        "project.read", "project.write", "project.delete", "project.settings",
        "members.read", "members.invite", "members.remove", "members.change_role",
        "snapshot.read", "snapshot.create", "snapshot.delete",
        "changeset.read", "changeset.create", "changeset.apply", "changeset.rollback", "changeset.commit",
        "ai.chat", "ai.propose",
    },
    "admin": {
        "project.read", "project.write", "project.settings",
        "members.read", "members.invite", "members.remove",
        "snapshot.read", "snapshot.create", "snapshot.delete",
        "changeset.read", "changeset.create", "changeset.apply", "changeset.rollback", "changeset.commit",
        "ai.chat", "ai.propose",
    },
    "editor": {
        "project.read", "project.write",
        "members.read",
        "snapshot.read", "snapshot.create",
        "changeset.read", "changeset.create", "changeset.apply", "changeset.rollback",
        "ai.chat", "ai.propose",
    },
    "viewer": {
        "project.read",
        "members.read",
        "snapshot.read",
        "changeset.read",
        "ai.chat",
    },
}


def has_permission(role: str, permission: str) -> bool:
    """Check if a role has a specific permission"""
    return permission in ROLE_PERMISSIONS.get(role, set())
