"""
CodeAtlas API - Code Analysis Platform Backend
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import projects, snapshots, files, symbols, ai, changesets
from app.core.config import settings

app = FastAPI(
    title="CodeAtlas API",
    description="Code analysis platform providing codebase context, AI assistance, and safe file modifications",
    version="0.1.0",
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "name": "CodeAtlas API",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Register routers
app.include_router(projects.router, prefix="/projects", tags=["Projects"])
app.include_router(snapshots.router, prefix="/snapshots", tags=["Snapshots"])
app.include_router(files.router, prefix="/snapshots/{snapshot_id}/files", tags=["Files"])
app.include_router(symbols.router, prefix="/snapshots/{snapshot_id}/symbols", tags=["Symbols"])
app.include_router(ai.router, prefix="/snapshots/{snapshot_id}/ai", tags=["AI"])
app.include_router(changesets.router, prefix="/changesets", tags=["ChangeSets"])
