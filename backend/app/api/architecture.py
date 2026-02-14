"""
Architecture API - Auto Architecture Summary

Exposes architecture analysis endpoints:
- GET  /architecture        — Raw aggregated architecture data
- GET  /architecture/summary — Template-based human-readable summary
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.snapshot import Snapshot
from app.services.architecture_service import ArchitectureService

router = APIRouter()


# ── Response Schemas ─────────────────────────────────────────────

class SystemOverviewResponse(BaseModel):
    top_folders: List[str]
    file_count: int
    total_lines: int
    languages: Dict[str, int]
    entry_points: List[str]
    tech_hints: List[str]


class FolderBreakdownResponse(BaseModel):
    path: str
    name: str
    file_count: int
    total_lines: int
    languages: Dict[str, int]
    purpose: str
    key_files: List[str]
    depth: int


class BackendFrontendResponse(BaseModel):
    api_paths: List[str]
    client_paths: List[str]
    boundary_files: List[str]
    api_file_count: int
    client_file_count: int


class TableSchemaResponse(BaseModel):
    name: str
    columns: List[str]
    relationships: List[str]
    source_file: str


class ArchitectureDataResponse(BaseModel):
    system_overview: SystemOverviewResponse
    folder_breakdown: List[FolderBreakdownResponse]
    backend_frontend: BackendFrontendResponse
    database_schema: List[TableSchemaResponse]


class ArchitectureSummaryResponse(BaseModel):
    """Human-readable architecture summary"""
    title: str
    system_overview: str
    folder_breakdown: str
    backend_frontend: str
    database_schema: str
    raw: ArchitectureDataResponse


# ── Helper: generate template summary ────────────────────────────

def _generate_template_summary(data: Dict[str, Any]) -> Dict[str, str]:
    """Generate a human-readable summary from raw architecture data (no AI needed)"""

    overview = data["system_overview"]
    folders = data["folder_breakdown"]
    bf = data["backend_frontend"]
    schema = data["database_schema"]

    # ── System overview ──
    langs_sorted = sorted(overview["languages"].items(), key=lambda x: -x[1])
    lang_str = ", ".join(f"{lang} ({count} files)" for lang, count in langs_sorted[:5])
    entry_str = ", ".join(f"`{e}`" for e in overview["entry_points"][:5]) or "None detected"
    tech_str = ", ".join(overview["tech_hints"]) or "Not detected"

    system_text = (
        f"The project contains **{overview['file_count']} files** "
        f"with **{overview['total_lines']:,} lines** of code across "
        f"**{len(overview['top_folders'])} top-level folders** "
        f"({', '.join(overview['top_folders'][:8])}).\n\n"
        f"**Languages**: {lang_str}\n\n"
        f"**Tech stack hints**: {tech_str}\n\n"
        f"**Entry points**: {entry_str}"
    )

    # ── Folder breakdown ──
    # Only show folders with files, sorted by file count
    significant = [f for f in folders if f["file_count"] > 0]
    significant.sort(key=lambda x: -x["file_count"])

    folder_lines = []
    for f in significant[:15]:
        indent = "  " * f["depth"]
        folder_lines.append(
            f"{indent}- **{f['name']}/** — {f['purpose']} "
            f"({f['file_count']} files, {f['total_lines']:,} lines)"
        )
    folder_text = "\n".join(folder_lines) if folder_lines else "No folder structure detected."

    # ── Backend / Frontend ──
    if bf["api_file_count"] > 0 or bf["client_file_count"] > 0:
        bf_text = (
            f"**Backend files**: {bf['api_file_count']} files detected in API/server paths\n\n"
            f"**Frontend files**: {bf['client_file_count']} files detected in client/UI paths\n\n"
        )
        if bf["boundary_files"]:
            boundary_list = ", ".join(f"`{b}`" for b in bf["boundary_files"][:10])
            bf_text += f"**API boundary files** (where backend meets frontend): {boundary_list}"
        else:
            bf_text += "No explicit API boundary files detected."
    else:
        bf_text = "No clear backend/frontend separation detected. This may be a single-tier application."

    # ── Database schema ──
    if schema:
        schema_lines = []
        for t in schema[:20]:
            cols = ", ".join(t["columns"][:8])
            if len(t["columns"]) > 8:
                cols += f"... (+{len(t['columns']) - 8} more)"
            rels = ""
            if t["relationships"]:
                rels = f" | Relationships: {', '.join(t['relationships'])}"
            schema_lines.append(f"- **{t['name']}** — columns: {cols}{rels}\n  Source: `{t['source_file']}`")
        schema_text = "\n".join(schema_lines)
    else:
        schema_text = "No database models detected. The project may not use an ORM, or models are in an unrecognized pattern."

    return {
        "system_overview": system_text,
        "folder_breakdown": folder_text,
        "backend_frontend": bf_text,
        "database_schema": schema_text,
    }


# ── Endpoints ────────────────────────────────────────────────────

@router.get("", response_model=ArchitectureDataResponse)
async def get_architecture(
    snapshot_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get raw architecture data for a snapshot.

    Returns aggregated data about:
    - System overview (files, languages, entry points)
    - Folder responsibilities
    - Backend/frontend boundaries
    - Database schema (inferred from models)
    """
    # Verify snapshot exists
    result = await db.execute(
        select(Snapshot).where(Snapshot.id == snapshot_id)
    )
    snapshot = result.scalar_one_or_none()
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    service = ArchitectureService(db, snapshot_id)
    data = await service.aggregate()
    return service.to_dict(data)


@router.get("/summary", response_model=ArchitectureSummaryResponse)
async def get_architecture_summary(
    snapshot_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a human-readable architecture summary.

    Returns both raw data and template-generated text summaries
    for system overview, folder breakdown, backend/frontend boundaries,
    and database schema.
    """
    # Verify snapshot exists
    result = await db.execute(
        select(Snapshot).where(Snapshot.id == snapshot_id)
    )
    snapshot = result.scalar_one_or_none()
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    service = ArchitectureService(db, snapshot_id)
    data = await service.aggregate()
    raw = service.to_dict(data)

    # Generate template-based summary
    summaries = _generate_template_summary(raw)

    return ArchitectureSummaryResponse(
        title=f"Architecture Summary",
        system_overview=summaries["system_overview"],
        folder_breakdown=summaries["folder_breakdown"],
        backend_frontend=summaries["backend_frontend"],
        database_schema=summaries["database_schema"],
        raw=raw,
    )
