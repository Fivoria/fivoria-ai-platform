"""
WebSocket Manager for real-time event streaming
"""

import asyncio
import json
from typing import Dict, Set, Optional, Any
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
import logging

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections for real-time event streaming"""
    
    def __init__(self):
        # Store active connections: {user_id: {connection_id: WebSocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        # Store task subscriptions: {task_id: {user_id}}
        self.task_subscriptions: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str, connection_id: str):
        """Accept and store a new WebSocket connection"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = {}
        
        self.active_connections[user_id][connection_id] = websocket
        logger.info(f"WebSocket connected: user_id={user_id}, connection_id={connection_id}")
        
        # Send welcome message
        await self.send_personal_message(
            {
                "type": "connected",
                "timestamp": datetime.utcnow().isoformat(),
                "connection_id": connection_id
            },
            user_id,
            connection_id
        )
    
    def disconnect(self, user_id: str, connection_id: str):
        """Remove a WebSocket connection"""
        if user_id in self.active_connections and connection_id in self.active_connections[user_id]:
            del self.active_connections[user_id][connection_id]
            
            # Clean up empty user entries
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
            
            logger.info(f"WebSocket disconnected: user_id={user_id}, connection_id={connection_id}")
    
    async def send_personal_message(self, message: Dict[str, Any], user_id: str, connection_id: str):
        """Send a message to a specific connection"""
        if user_id in self.active_connections and connection_id in self.active_connections[user_id]:
            websocket = self.active_connections[user_id][connection_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to {connection_id}: {e}")
                self.disconnect(user_id, connection_id)
    
    async def broadcast_to_user(self, message: Dict[str, Any], user_id: str):
        """Broadcast a message to all connections for a user"""
        if user_id in self.active_connections:
            disconnected_connections = []
            
            for connection_id, websocket in self.active_connections[user_id].items():
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to broadcast to {connection_id}: {e}")
                    disconnected_connections.append(connection_id)
            
            # Clean up disconnected connections
            for connection_id in disconnected_connections:
                self.disconnect(user_id, connection_id)
    
    async def broadcast_to_all(self, message: Dict[str, Any]):
        """Broadcast a message to all active connections"""
        for user_id in list(self.active_connections.keys()):
            await self.broadcast_to_user(message, user_id)
    
    def subscribe_to_task(self, task_id: str, user_id: str):
        """Subscribe a user to task events"""
        if task_id not in self.task_subscriptions:
            self.task_subscriptions[task_id] = set()
        
        self.task_subscriptions[task_id].add(user_id)
        logger.info(f"User {user_id} subscribed to task {task_id}")
    
    def unsubscribe_from_task(self, task_id: str, user_id: str):
        """Unsubscribe a user from task events"""
        if task_id in self.task_subscriptions and user_id in self.task_subscriptions[task_id]:
            self.task_subscriptions[task_id].remove(user_id)
            
            # Clean up empty task entries
            if not self.task_subscriptions[task_id]:
                del self.task_subscriptions[task_id]
            
            logger.info(f"User {user_id} unsubscribed from task {task_id}")
    
    async def send_task_event(self, task_id: str, event: Dict[str, Any]):
        """Send an event to all subscribers of a task"""
        if task_id in self.task_subscriptions:
            message = {
                "type": "task_event",
                "task_id": task_id,
                "timestamp": datetime.utcnow().isoformat(),
                "event": event
            }
            
            for user_id in self.task_subscriptions[task_id]:
                await self.broadcast_to_user(message, user_id)
    
    def get_connection_count(self, user_id: Optional[str] = None) -> int:
        """Get count of active connections"""
        if user_id:
            return len(self.active_connections.get(user_id, {}))
        
        return sum(len(conns) for conns in self.active_connections.values())
    
    def get_user_ids(self) -> Set[str]:
        """Get all connected user IDs"""
        return set(self.active_connections.keys())


# Global WebSocket manager instance
websocket_manager = WebSocketManager()
