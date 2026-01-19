"""
Symbol and Reference models - represents code symbols and their relationships
"""

from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Integer, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
import enum

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.snapshot import Snapshot
    from app.models.file import File


class SymbolKind(str, enum.Enum):
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    PROPERTY = "property"
    VARIABLE = "variable"
    CONSTANT = "constant"
    INTERFACE = "interface"
    TYPE = "type"
    ENUM = "enum"
    IMPORT = "import"


class ReferenceKind(str, enum.Enum):
    IMPORT = "import"
    CALL = "call"
    USAGE = "usage"
    INHERITANCE = "inheritance"
    IMPLEMENTATION = "implementation"
    TYPE_REFERENCE = "type_reference"


class Symbol(Base, TimestampMixin):
    __tablename__ = "symbols"

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
    
    # Symbol identification
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    qualified_name: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    kind: Mapped[SymbolKind] = mapped_column(SQLEnum(SymbolKind), nullable=False)
    
    # Location in file
    start_line: Mapped[int] = mapped_column(Integer, nullable=False)
    start_col: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    end_line: Mapped[int] = mapped_column(Integer, nullable=False)
    end_col: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Signature and documentation
    signature: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    docstring: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Parent symbol (for nested definitions)
    parent_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("symbols.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Relationships
    snapshot: Mapped["Snapshot"] = relationship("Snapshot", back_populates="symbols")
    file: Mapped["File"] = relationship("File", back_populates="symbols")
    
    # References where this symbol is the source
    outgoing_refs: Mapped[List["Reference"]] = relationship(
        "Reference",
        foreign_keys="Reference.from_symbol_id",
        back_populates="from_symbol",
        cascade="all, delete-orphan",
    )
    
    # References where this symbol is the target
    incoming_refs: Mapped[List["Reference"]] = relationship(
        "Reference",
        foreign_keys="Reference.to_symbol_id",
        back_populates="to_symbol",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Symbol {self.kind.value} {self.name}>"


class Reference(Base, TimestampMixin):
    __tablename__ = "references"

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
    
    # Source symbol
    from_symbol_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("symbols.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Target (symbol or file for external imports)
    to_symbol_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("symbols.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    to_file_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("files.id", ondelete="CASCADE"),
        nullable=True,
    )
    
    # Reference kind
    kind: Mapped[ReferenceKind] = mapped_column(SQLEnum(ReferenceKind), nullable=False)
    
    # Location of the reference
    line: Mapped[int] = mapped_column(Integer, nullable=False)
    column: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Relationships
    from_symbol: Mapped["Symbol"] = relationship(
        "Symbol",
        foreign_keys=[from_symbol_id],
        back_populates="outgoing_refs",
    )
    to_symbol: Mapped[Optional["Symbol"]] = relationship(
        "Symbol",
        foreign_keys=[to_symbol_id],
        back_populates="incoming_refs",
    )

    def __repr__(self) -> str:
        return f"<Reference {self.kind.value} from {self.from_symbol_id[:8]}>"
