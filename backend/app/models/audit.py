"""
Audit Log model - track all actions for compliance and debugging
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Text, DateTime, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class AuditLog(Base):
    """Audit log entry for tracking user actions"""
    __tablename__ = "audit_logs"
    
    # Composite index for efficient querying
    __table_args__ = (
        Index("ix_audit_logs_user_created", "user_id", "created_at"),
        Index("ix_audit_logs_project_created", "project_id", "created_at"),
        Index("ix_audit_logs_action_created", "action", "created_at"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    
    # Who performed the action
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
        index=True,
    )
    
    # What action was performed
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # Resource type and ID
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)  # project, snapshot, changeset, etc.
    resource_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # Optional project context
    project_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    
    # Details about the action
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Additional metadata (JSON for flexibility)
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Request context
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )
    
    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} by {self.user_id} at {self.created_at}>"


# Standard audit actions
class AuditAction:
    """Standard audit action constants"""
    # Authentication
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_REGISTER = "user.register"
    USER_PASSWORD_CHANGE = "user.password_change"
    
    # Projects
    PROJECT_CREATE = "project.create"
    PROJECT_UPDATE = "project.update"
    PROJECT_DELETE = "project.delete"
    PROJECT_IMPORT = "project.import"
    
    # Memberships
    MEMBER_INVITE = "member.invite"
    MEMBER_ACCEPT = "member.accept"
    MEMBER_REMOVE = "member.remove"
    MEMBER_ROLE_CHANGE = "member.role_change"
    
    # Snapshots
    SNAPSHOT_CREATE = "snapshot.create"
    SNAPSHOT_DELETE = "snapshot.delete"
    SNAPSHOT_INDEX_START = "snapshot.index_start"
    SNAPSHOT_INDEX_COMPLETE = "snapshot.index_complete"
    
    # ChangeSets
    CHANGESET_CREATE = "changeset.create"
    CHANGESET_APPLY = "changeset.apply"
    CHANGESET_ROLLBACK = "changeset.rollback"
    CHANGESET_COMMIT = "changeset.commit"
    CHANGESET_DELETE = "changeset.delete"
    
    # AI
    AI_CHAT = "ai.chat"
    AI_EXPLAIN = "ai.explain"
    AI_PROPOSE = "ai.propose"
    
    # Files
    FILE_VIEW = "file.view"
    FILE_DOWNLOAD = "file.download"
