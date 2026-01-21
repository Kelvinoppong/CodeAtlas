"""
Audit Service - logging user actions for compliance and debugging
"""

from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog


class AuditService:
    """Service for logging audit events"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def log(
        self,
        action: str,
        resource_type: str,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        project_id: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """
        Log an audit event.
        
        Args:
            action: The action performed (use AuditAction constants)
            resource_type: Type of resource (project, snapshot, changeset, etc.)
            user_id: ID of the user who performed the action
            resource_id: ID of the affected resource
            project_id: ID of the project context (if applicable)
            description: Human-readable description
            metadata: Additional data as JSON
            ip_address: Client IP address
            user_agent: Client user agent string
        
        Returns:
            The created AuditLog entry
        """
        audit_log = AuditLog(
            action=action,
            resource_type=resource_type,
            user_id=user_id,
            resource_id=resource_id,
            project_id=project_id,
            description=description,
            metadata=metadata,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.now(timezone.utc),
        )
        
        self.db.add(audit_log)
        await self.db.flush()
        
        return audit_log
    
    async def log_auth(
        self,
        action: str,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        failure_reason: Optional[str] = None,
    ) -> AuditLog:
        """Log an authentication event"""
        metadata = {"success": success}
        if failure_reason:
            metadata["failure_reason"] = failure_reason
        
        return await self.log(
            action=action,
            resource_type="auth",
            user_id=user_id if success else None,
            description=f"Authentication {'succeeded' if success else 'failed'}",
            metadata=metadata,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    
    async def log_project(
        self,
        action: str,
        project_id: str,
        user_id: str,
        description: Optional[str] = None,
        metadata: Optional[dict] = None,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        """Log a project-related event"""
        return await self.log(
            action=action,
            resource_type="project",
            resource_id=project_id,
            project_id=project_id,
            user_id=user_id,
            description=description,
            metadata=metadata,
            ip_address=ip_address,
        )
    
    async def log_changeset(
        self,
        action: str,
        changeset_id: str,
        project_id: str,
        user_id: str,
        description: Optional[str] = None,
        metadata: Optional[dict] = None,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        """Log a changeset-related event"""
        return await self.log(
            action=action,
            resource_type="changeset",
            resource_id=changeset_id,
            project_id=project_id,
            user_id=user_id,
            description=description,
            metadata=metadata,
            ip_address=ip_address,
        )
