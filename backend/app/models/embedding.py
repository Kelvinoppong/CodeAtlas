"""
EmbeddingChunk model - for vector similarity search
"""

from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Text, ForeignKey, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.snapshot import Snapshot
    from app.models.file import File


class EmbeddingChunk(Base, TimestampMixin):
    __tablename__ = "embedding_chunks"

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
    file_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Chunk position within file
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    start_line: Mapped[int] = mapped_column(Integer, nullable=False)
    end_line: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # The actual text content
    text: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Token count (for context window management)
    token_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Embedding vector stored as binary (install pgvector for vector search)
    # Format: numpy array serialized with np.tobytes()
    embedding: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    
    # Optional: symbol this chunk is primarily about
    primary_symbol_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("symbols.id", ondelete="SET NULL"),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<EmbeddingChunk {self.file_id[:8]} chunk {self.chunk_index}>"
