from typing import Dict, Set
from fastapi import WebSocket
import json
import asyncio
from datetime import datetime


class WebSocketManager:
    """Manages WebSocket connections for video processing updates"""
    
    def __init__(self):
        # video_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()
    
    async def connect(self, video_id: str, websocket: WebSocket):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        async with self._lock:
            if video_id not in self.active_connections:
                self.active_connections[video_id] = set()
            self.active_connections[video_id].add(websocket)
        print(f"WebSocket connected for video {video_id}. Total connections: {len(self.active_connections[video_id])}")
    
    async def disconnect(self, video_id: str, websocket: WebSocket):
        """Remove a WebSocket connection"""
        async with self._lock:
            if video_id in self.active_connections:
                self.active_connections[video_id].discard(websocket)
                if not self.active_connections[video_id]:
                    del self.active_connections[video_id]
        print(f"WebSocket disconnected for video {video_id}")
    
    async def broadcast(self, video_id: str, message: dict):
        """Broadcast a message to all connections for a video"""
        if video_id not in self.active_connections:
            return
        
        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat()
        
        message_json = json.dumps(message)
        
        # Send to all active connections (iterate over a copy to avoid set modification during iteration)
        disconnected = set()
        for websocket in list(self.active_connections[video_id]):
            try:
                await websocket.send_text(message_json)
            except Exception as e:
                print(f"Error sending to WebSocket: {e}")
                disconnected.add(websocket)
        
        # Clean up disconnected websockets
        if disconnected:
            async with self._lock:
                self.active_connections[video_id] -= disconnected
                if not self.active_connections[video_id]:
                    del self.active_connections[video_id]
    
    async def send_progress(self, video_id: str, stage: str, progress: int, message: str):
        """Send progress update to all connections for a video"""
        await self.broadcast(video_id, {
            "type": "progress",
            "stage": stage,
            "progress": progress,
            "message": message
        })
    
    async def send_message(self, video_id: str, message: dict):
        """Send custom message to all connections for a video"""
        await self.broadcast(video_id, message)
    
    async def send_stage_complete(self, video_id: str, current_stage: str, next_stage: str):
        """Send stage completion notification"""
        await self.broadcast(video_id, {
            "type": "stage_complete",
            "current_stage": current_stage,
            "next_stage": next_stage
        })
    
    async def send_complete(self, video_id: str, ideas_count: int):
        """Send processing completion notification"""
        await self.broadcast(video_id, {
            "type": "complete",
            "message": f"Processing complete! {ideas_count} ideas generated.",
            "ideas_count": ideas_count
        })
    
    async def send_error(self, video_id: str, stage: str, error: str, details: str):
        """Send error notification"""
        await self.broadcast(video_id, {
            "type": "error",
            "stage": stage,
            "error": error,
            "message": details
        })


# Global WebSocket manager instance
ws_manager = WebSocketManager()
