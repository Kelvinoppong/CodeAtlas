"""
AI chat and explanation endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid
import httpx

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.config import settings
from app.models.snapshot import Snapshot
from app.models.file import File
from app.models.symbol import Symbol, SymbolKind
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatMessage(BaseModel):
    role: str  # user, assistant
    content: str
    citations: Optional[List[dict]] = None


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    context_file: Optional[str] = None  # Optional file to include as context


class ChatResponse(BaseModel):
    session_id: str
    message: ChatMessage


class ExplainRequest(BaseModel):
    target: str  # file path, symbol id, or "system"
    question: Optional[str] = None


class ExplainResponse(BaseModel):
    explanation: str
    citations: List[dict]
    suggested_graph: Optional[dict] = None


class ProposeChangesRequest(BaseModel):
    instruction: str
    files: Optional[List[str]] = None


class ChangeProposal(BaseModel):
    changeset_id: str
    title: str
    rationale: str
    patches: List[dict]
    impacted_files: List[str]


async def call_ollama(prompt: str, context: str = "") -> str:
    """Call local Ollama server for chat completion"""
    url = f"{settings.OLLAMA_BASE_URL}/api/generate"
    
    full_prompt = prompt
    if context:
        full_prompt = f"""You are CodeAtlas, an AI assistant that helps developers understand and navigate codebases.

Here is some context about the codebase:
{context}

User question: {prompt}

Please provide a helpful, concise response. If referencing code, mention the file paths."""

    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 2048,
        }
    }
    
    async with httpx.AsyncClient(timeout=300.0) as client:  # 5 min timeout for large contexts
        try:
            response = await client.post(url, json=payload)
            
            if response.status_code != 200:
                error_detail = response.text
                raise HTTPException(status_code=500, detail=f"Ollama error: {error_detail}")
            
            data = response.json()
            return data.get("response", "")
        except httpx.ConnectError:
            raise HTTPException(status_code=500, detail="Ollama server not running. Start it with: ollama serve")


async def call_gemini(prompt: str, context: str = "") -> str:
    """Call Gemini API for chat completion"""
    if not settings.GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API key not configured")
    
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={settings.GEMINI_API_KEY}"
    
    full_prompt = prompt
    if context:
        full_prompt = f"""You are CodeAtlas, an AI assistant that helps developers understand and navigate codebases.

Here is some context about the codebase:
{context}

User question: {prompt}

Please provide a helpful, concise response. If referencing code, mention the file paths."""

    payload = {
        "contents": [{
            "parts": [{"text": full_prompt}]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 2048,
        }
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=payload)
        
        if response.status_code != 200:
            error_detail = response.text
            raise HTTPException(status_code=500, detail=f"Gemini API error: {error_detail}")
        
        data = response.json()
        
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as e:
            raise HTTPException(status_code=500, detail=f"Unexpected Gemini response format: {data}")


async def call_llm(prompt: str, context: str = "") -> str:
    """Call the configured LLM provider"""
    provider = settings.AI_PROVIDER.lower()
    
    if provider == "ollama":
        return await call_ollama(prompt, context)
    elif provider == "gemini":
        return await call_gemini(prompt, context)
    else:
        raise HTTPException(status_code=500, detail=f"Unknown AI provider: {provider}")


async def get_codebase_context(db: AsyncSession, snapshot_id: str, file_path: Optional[str] = None) -> str:
    """Get relevant codebase context for AI"""
    # Get snapshot
    result = await db.execute(select(Snapshot).where(Snapshot.id == snapshot_id))
    snapshot = result.scalar_one_or_none()
    
    if not snapshot:
        return ""
    
    context_parts = [f"Project snapshot with {snapshot.file_count} files and {snapshot.symbol_count} symbols."]
    
    # If a specific file is requested, include its content
    if file_path:
        result = await db.execute(
            select(File).where(
                File.snapshot_id == snapshot_id,
                File.path == file_path
            )
        )
        file = result.scalar_one_or_none()
        if file and file.content:
            context_parts.append(f"\nFile: {file.path}\n```{file.language or ''}\n{file.content[:4000]}\n```")
    
    # Get list of files
    result = await db.execute(
        select(File.path, File.language).where(File.snapshot_id == snapshot_id).limit(50)
    )
    files = result.all()
    if files:
        file_list = ", ".join([f.path for f in files[:20]])
        context_parts.append(f"\nProject files: {file_list}")
    
    # Get key symbols
    result = await db.execute(
        select(Symbol.name, Symbol.kind, Symbol.qualified_name)
        .where(Symbol.snapshot_id == snapshot_id)
        .where(Symbol.kind.in_([SymbolKind.CLASS, SymbolKind.FUNCTION]))
        .limit(30)
    )
    symbols = result.all()
    if symbols:
        symbol_list = ", ".join([f"{s.name} ({s.kind.value})" for s in symbols[:15]])
        context_parts.append(f"\nKey symbols: {symbol_list}")
    
    return "\n".join(context_parts)


@router.post("/chat", response_model=ChatResponse)
async def chat(
    snapshot_id: str,
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """Chat with AI about the codebase"""
    session_id = request.session_id or str(uuid.uuid4())
    
    try:
        # Get codebase context
        context = await get_codebase_context(db, snapshot_id, request.context_file)
        
        # Call LLM (Ollama or Gemini based on config)
        response_text = await call_llm(request.message, context)
        
        return ChatResponse(
            session_id=session_id,
            message=ChatMessage(
                role="assistant",
                content=response_text,
                citations=[],
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        # Fallback response if API fails
        logger.exception(f"Chat error: {e}")
        error_msg = str(e) if str(e) else type(e).__name__
        return ChatResponse(
            session_id=session_id,
            message=ChatMessage(
                role="assistant",
                content=f"I encountered an error processing your request: {error_msg}. Please try again.",
                citations=[],
            ),
        )


@router.post("/explain", response_model=ExplainResponse)
async def explain(
    snapshot_id: str,
    request: ExplainRequest,
    db: AsyncSession = Depends(get_db),
):
    """Get AI explanation of a file, symbol, or the system"""
    try:
        # Get file content if target is a file path
        file_content = ""
        if "/" in request.target or request.target.endswith(".py") or request.target.endswith(".ts"):
            result = await db.execute(
                select(File).where(
                    File.snapshot_id == snapshot_id,
                    File.path == request.target
                )
            )
            file = result.scalar_one_or_none()
            if file and file.content:
                file_content = f"File: {file.path}\n```{file.language or ''}\n{file.content[:6000]}\n```"
        
        question = request.question or f"Explain this code: {request.target}"
        prompt = f"{question}\n\n{file_content}" if file_content else question
        
        explanation = await call_llm(prompt, "")
        
        return ExplainResponse(
            explanation=explanation,
            citations=[{"file": request.target}] if "/" in request.target else [],
            suggested_graph=None,
        )
    except HTTPException:
        raise
    except Exception as e:
        return ExplainResponse(
            explanation=f"Error generating explanation: {str(e)}",
            citations=[],
            suggested_graph=None,
        )


@router.post("/propose-changes", response_model=ChangeProposal)
async def propose_changes(
    snapshot_id: str,
    request: ProposeChangesRequest,
    db: AsyncSession = Depends(get_db),
):
    """Have AI propose code changes"""
    changeset_id = str(uuid.uuid4())
    
    # Get context for the files
    context_parts = []
    if request.files:
        for file_path in request.files[:5]:  # Limit to 5 files
            result = await db.execute(
                select(File).where(
                    File.snapshot_id == snapshot_id,
                    File.path == file_path
                )
            )
            file = result.scalar_one_or_none()
            if file and file.content:
                context_parts.append(f"File: {file.path}\n```{file.language or ''}\n{file.content[:3000]}\n```")
    
    context = "\n\n".join(context_parts)
    prompt = f"Propose code changes for: {request.instruction}\n\nDescribe what changes should be made and why."
    
    try:
        rationale = await call_llm(prompt, context)
    except Exception:
        rationale = "Unable to generate AI proposal. Please try again."
    
    return ChangeProposal(
        changeset_id=changeset_id,
        title=f"AI Proposed: {request.instruction[:50]}...",
        rationale=rationale,
        patches=[],
        impacted_files=request.files or [],
    )
