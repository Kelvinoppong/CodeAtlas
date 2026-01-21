"""
WebSocket API for real-time collaboration
"""

import json
import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Set
from dataclasses import dataclass, field, asdict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db, async_session_maker
from app.models.user import User
from app.services.auth_service import auth_service

router = APIRouter()


# ============ Connection Manager ============

@dataclass
class UserPresence:
    """User presence information"""
    user_id: str
    user_name: str
    avatar_url: Optional[str]
    connected_at: datetime
    current_file: Optional[str] = None
    cursor_line: Optional[int] = None
    cursor_col: Optional[int] = None
    color: str = "#a78bfa"  # Default purple


@dataclass
class ProjectRoom:
    """A room for a project with connected users"""
    project_id: str
    connections: Dict[str, WebSocket] = field(default_factory=dict)
    presence: Dict[str, UserPresence] = field(default_factory=dict)


class ConnectionManager:
    """Manages WebSocket connections for real-time collaboration"""
    
    def __init__(self):
        # project_id -> ProjectRoom
        self.rooms: Dict[str, ProjectRoom] = {}
        # user_id -> set of project_ids they're connected to
        self.user_rooms: Dict[str, Set[str]] = {}
        # Assign colors to users
        self.colors = [
            "#a78bfa", "#f472b6", "#34d399", "#fbbf24", 
            "#60a5fa", "#f87171", "#a3e635", "#22d3ee",
        ]
        self.color_index = 0
    
    def _get_next_color(self) -> str:
        """Get the next color for a new user"""
        color = self.colors[self.color_index % len(self.colors)]
        self.color_index += 1
        return color
    
    async def connect(
        self,
        websocket: WebSocket,
        project_id: str,
        user: User,
    ) -> None:
        """Connect a user to a project room"""
        await websocket.accept()
        
        # Get or create room
        if project_id not in self.rooms:
            self.rooms[project_id] = ProjectRoom(project_id=project_id)
        
        room = self.rooms[project_id]
        
        # Create presence
        presence = UserPresence(
            user_id=user.id,
            user_name=user.name,
            avatar_url=user.avatar_url,
            connected_at=datetime.now(timezone.utc),
            color=self._get_next_color(),
        )
        
        # Add to room
        room.connections[user.id] = websocket
        room.presence[user.id] = presence
        
        # Track user rooms
        if user.id not in self.user_rooms:
            self.user_rooms[user.id] = set()
        self.user_rooms[user.id].add(project_id)
        
        # Broadcast join to others
        await self.broadcast(
            project_id,
            {
                "type": "user_joined",
                "user": asdict(presence),
                "users": [asdict(p) for p in room.presence.values()],
            },
            exclude=user.id,
        )
        
        # Send current room state to the new user
        await websocket.send_json({
            "type": "room_state",
            "project_id": project_id,
            "users": [asdict(p) for p in room.presence.values()],
        })
    
    async def disconnect(self, project_id: str, user_id: str) -> None:
        """Disconnect a user from a project room"""
        if project_id not in self.rooms:
            return
        
        room = self.rooms[project_id]
        
        # Remove from room
        room.connections.pop(user_id, None)
        presence = room.presence.pop(user_id, None)
        
        # Update user rooms
        if user_id in self.user_rooms:
            self.user_rooms[user_id].discard(project_id)
            if not self.user_rooms[user_id]:
                del self.user_rooms[user_id]
        
        # Clean up empty rooms
        if not room.connections:
            del self.rooms[project_id]
            return
        
        # Broadcast leave to others
        if presence:
            await self.broadcast(
                project_id,
                {
                    "type": "user_left",
                    "user_id": user_id,
                    "users": [asdict(p) for p in room.presence.values()],
                },
            )
    
    async def broadcast(
        self,
        project_id: str,
        message: dict,
        exclude: Optional[str] = None,
    ) -> None:
        """Broadcast a message to all users in a room"""
        if project_id not in self.rooms:
            return
        
        room = self.rooms[project_id]
        disconnected = []
        
        for user_id, websocket in room.connections.items():
            if user_id == exclude:
                continue
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(user_id)
        
        # Clean up disconnected users
        for user_id in disconnected:
            await self.disconnect(project_id, user_id)
    
    async def send_to_user(
        self,
        project_id: str,
        user_id: str,
        message: dict,
    ) -> bool:
        """Send a message to a specific user"""
        if project_id not in self.rooms:
            return False
        
        room = self.rooms[project_id]
        websocket = room.connections.get(user_id)
        
        if websocket:
            try:
                await websocket.send_json(message)
                return True
            except Exception:
                await self.disconnect(project_id, user_id)
        
        return False
    
    def update_presence(
        self,
        project_id: str,
        user_id: str,
        current_file: Optional[str] = None,
        cursor_line: Optional[int] = None,
        cursor_col: Optional[int] = None,
    ) -> Optional[UserPresence]:
        """Update a user's presence in a room"""
        if project_id not in self.rooms:
            return None
        
        room = self.rooms[project_id]
        presence = room.presence.get(user_id)
        
        if presence:
            if current_file is not None:
                presence.current_file = current_file
            if cursor_line is not None:
                presence.cursor_line = cursor_line
            if cursor_col is not None:
                presence.cursor_col = cursor_col
        
        return presence
    
    def get_room_users(self, project_id: str) -> list:
        """Get all users in a room"""
        if project_id not in self.rooms:
            return []
        return [asdict(p) for p in self.rooms[project_id].presence.values()]


# Global connection manager
manager = ConnectionManager()


# ============ WebSocket Endpoint ============

@router.websocket("/ws/{project_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    project_id: str,
    token: Optional[str] = None,
):
    """
    WebSocket endpoint for real-time collaboration.
    
    Connect with: ws://host/ws/{project_id}?token=<access_token>
    
    Message types (client -> server):
    - cursor_move: { type: "cursor_move", file: "path", line: 1, col: 1 }
    - file_open: { type: "file_open", file: "path" }
    - file_close: { type: "file_close", file: "path" }
    - chat: { type: "chat", message: "hello" }
    
    Message types (server -> client):
    - room_state: Initial state with all users
    - user_joined: New user connected
    - user_left: User disconnected
    - presence_update: User moved cursor or opened file
    - chat: Chat message from another user
    """
    # Authenticate
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return
    
    user_id = auth_service.verify_access_token(token)
    if not user_id:
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    # Get user from database
    async with async_session_maker() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            await websocket.close(code=4001, reason="User not found or inactive")
            return
        
        # TODO: Check if user has access to project
        
        # Connect to room
        await manager.connect(websocket, project_id, user)
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            if msg_type == "cursor_move":
                # Update presence and broadcast
                presence = manager.update_presence(
                    project_id,
                    user_id,
                    current_file=data.get("file"),
                    cursor_line=data.get("line"),
                    cursor_col=data.get("col"),
                )
                if presence:
                    await manager.broadcast(
                        project_id,
                        {
                            "type": "presence_update",
                            "user": asdict(presence),
                        },
                        exclude=user_id,
                    )
            
            elif msg_type == "file_open":
                presence = manager.update_presence(
                    project_id,
                    user_id,
                    current_file=data.get("file"),
                )
                if presence:
                    await manager.broadcast(
                        project_id,
                        {
                            "type": "presence_update",
                            "user": asdict(presence),
                        },
                        exclude=user_id,
                    )
            
            elif msg_type == "file_close":
                presence = manager.update_presence(
                    project_id,
                    user_id,
                    current_file=None,
                    cursor_line=None,
                    cursor_col=None,
                )
                if presence:
                    await manager.broadcast(
                        project_id,
                        {
                            "type": "presence_update",
                            "user": asdict(presence),
                        },
                        exclude=user_id,
                    )
            
            elif msg_type == "chat":
                # Broadcast chat message
                await manager.broadcast(
                    project_id,
                    {
                        "type": "chat",
                        "user_id": user_id,
                        "user_name": user.name,
                        "message": data.get("message", ""),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    exclude=user_id,
                )
            
            elif msg_type == "ping":
                # Respond to ping
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        await manager.disconnect(project_id, user_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        await manager.disconnect(project_id, user_id)


@router.get("/presence/{project_id}")
async def get_presence(project_id: str):
    """Get current presence for a project (REST fallback)"""
    return {
        "project_id": project_id,
        "users": manager.get_room_users(project_id),
    }
