"""
Pagination utilities for large repositories
"""

from typing import TypeVar, Generic, List, Optional, Any
from dataclasses import dataclass
from pydantic import BaseModel
from fastapi import Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select


T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination parameters from query string"""
    page: int = 1
    page_size: int = 50
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        return self.page_size


def get_pagination(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=500, description="Items per page"),
) -> PaginationParams:
    """FastAPI dependency for pagination parameters"""
    return PaginationParams(page=page, page_size=page_size)


@dataclass
class PaginatedResult(Generic[T]):
    """Paginated result with metadata"""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
    
    def to_dict(self) -> dict:
        return {
            "items": self.items,
            "pagination": {
                "total": self.total,
                "page": self.page,
                "page_size": self.page_size,
                "total_pages": self.total_pages,
                "has_next": self.has_next,
                "has_prev": self.has_prev,
            }
        }


class PaginatedResponse(BaseModel):
    """Pydantic model for paginated API responses"""
    items: List[Any]
    pagination: dict
    
    class Config:
        from_attributes = True


async def paginate(
    db: AsyncSession,
    query: Select,
    params: PaginationParams,
    count_query: Optional[Select] = None,
) -> PaginatedResult:
    """
    Execute a paginated query.
    
    Args:
        db: Database session
        query: SQLAlchemy select query
        params: Pagination parameters
        count_query: Optional custom count query (defaults to counting the main query)
    
    Returns:
        PaginatedResult with items and metadata
    """
    # Get total count
    if count_query is None:
        # Create count query from the main query
        count_query = select(func.count()).select_from(query.subquery())
    
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0
    
    # Apply pagination
    paginated_query = query.offset(params.offset).limit(params.limit)
    result = await db.execute(paginated_query)
    items = list(result.scalars().all())
    
    # Calculate metadata
    total_pages = (total + params.page_size - 1) // params.page_size if total > 0 else 0
    
    return PaginatedResult(
        items=items,
        total=total,
        page=params.page,
        page_size=params.page_size,
        total_pages=total_pages,
        has_next=params.page < total_pages,
        has_prev=params.page > 1,
    )


# ============ Cursor-based Pagination ============

class CursorParams(BaseModel):
    """Cursor-based pagination parameters"""
    cursor: Optional[str] = None
    limit: int = 50
    direction: str = "next"  # "next" or "prev"


def get_cursor_params(
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    limit: int = Query(50, ge=1, le=500, description="Items to return"),
    direction: str = Query("next", description="Direction: next or prev"),
) -> CursorParams:
    """FastAPI dependency for cursor pagination"""
    return CursorParams(cursor=cursor, limit=limit, direction=direction)


@dataclass
class CursorResult(Generic[T]):
    """Cursor-paginated result"""
    items: List[T]
    next_cursor: Optional[str]
    prev_cursor: Optional[str]
    has_more: bool
    
    def to_dict(self) -> dict:
        return {
            "items": self.items,
            "cursors": {
                "next": self.next_cursor,
                "prev": self.prev_cursor,
            },
            "has_more": self.has_more,
        }
