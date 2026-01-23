"""
CodeAtlas API - Code Analysis Platform Backend
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import projects, snapshots, files, symbols, ai, changesets, auth, websocket, system
from app.core.config import settings
from app.core.database import init_db, close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print("🚀 Starting CodeAtlas API...")
    try:
        await init_db()
        print("✅ Database initialized")
    except Exception as e:
        print(f"⚠️ Database initialization failed: {e}")
        print("   Make sure PostgreSQL is running (docker-compose up -d)")
    
    yield
    
    # Shutdown
    print("👋 Shutting down CodeAtlas API...")
    await close_db()


app = FastAPI(
    title="CodeAtlas API",
    description="Code analysis platform providing codebase context, AI assistance, and safe file modifications",
    version="0.2.0",
    lifespan=lifespan,
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
        "version": "0.2.0",
        "status": "running",
        "docs": "/docs",
        "features": [
            "Multi-user authentication",
            "Real-time collaboration",
            "Incremental indexing",
            "Safe code modifications",
        ],
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Register routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(projects.router, prefix="/projects", tags=["Projects"])
app.include_router(snapshots.router, prefix="/snapshots", tags=["Snapshots"])
app.include_router(files.router, prefix="/snapshots/{snapshot_id}/files", tags=["Files"])
app.include_router(symbols.router, prefix="/snapshots/{snapshot_id}/symbols", tags=["Symbols"])
app.include_router(ai.router, prefix="/snapshots/{snapshot_id}/ai", tags=["AI"])
app.include_router(changesets.router, prefix="/changesets", tags=["ChangeSets"])
app.include_router(system.router, prefix="/system", tags=["System"])
app.include_router(websocket.router, tags=["WebSocket"])
