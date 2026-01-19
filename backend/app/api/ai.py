"""
AI chat and explanation endpoints
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid

router = APIRouter()


class ChatMessage(BaseModel):
    role: str  # user, assistant
    content: str
    citations: Optional[List[dict]] = None


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


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
    files: Optional[List[str]] = None  # Limit to specific files


class ChangeProposal(BaseModel):
    changeset_id: str
    title: str
    rationale: str
    patches: List[dict]
    impacted_files: List[str]


@router.post("/chat", response_model=ChatResponse)
async def chat(snapshot_id: str, request: ChatRequest):
    """Chat with AI about the codebase"""
    session_id = request.session_id or str(uuid.uuid4())
    
    # Demo response
    response_content = """It looks like you're talking about a Minesweeper game! It's a classic game of logic and deduction. Here's a breakdown of how it works:

1. **Initialization:** The game starts by creating a grid of cells, with a hidden number of mines randomly placed within the grid.

2. **Player's Turn:** The player clicks on a cell.

   • **If the cell contains a mine:** The game is over, and the player loses.
   
   • **If the cell is safe:** The cell is revealed, and the number of adjacent mines is displayed."""

    return ChatResponse(
        session_id=session_id,
        message=ChatMessage(
            role="assistant",
            content=response_content,
            citations=[
                {"file": "minesweeper/minesweeper.py", "lines": "1-45"},
                {"file": "minesweeper/assets/images/mine.png"},
            ],
        ),
    )


@router.post("/explain", response_model=ExplainResponse)
async def explain(snapshot_id: str, request: ExplainRequest):
    """Get AI explanation of a file, symbol, or the system"""
    
    return ExplainResponse(
        explanation="""This is a Minesweeper game implementation in Python.

**Key Components:**
- `Minesweeper` class: Main game logic
- `__init__`: Sets up the board with random mine placement
- `nearby_mines`: Counts adjacent mines for a cell
- `won`: Checks victory condition

The game uses a 2D grid (self.board) where True = mine, False = safe.""",
        citations=[
            {"file": "minesweeper/minesweeper.py", "lines": "1-75"},
        ],
        suggested_graph={
            "type": "dependency",
            "root": "Minesweeper",
        },
    )


@router.post("/propose-changes", response_model=ChangeProposal)
async def propose_changes(snapshot_id: str, request: ProposeChangesRequest):
    """Have AI propose code changes"""
    changeset_id = str(uuid.uuid4())
    
    return ChangeProposal(
        changeset_id=changeset_id,
        title=f"AI Proposed: {request.instruction[:50]}...",
        rationale="Based on your request, here are the proposed changes.",
        patches=[],  # Would contain actual diffs
        impacted_files=request.files or [],
    )
