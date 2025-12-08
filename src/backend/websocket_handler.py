"""
WebSocket Handler for Real-time Sentiment Streaming
Enables real-time sentiment updates to connected clients
"""

import asyncio
import json
from typing import Set, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger
from datetime import datetime

from src.backend.sentiment_pipeline import SentimentPipeline


class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.logger = logger.bind(component="ConnectionManager")
    
    async def connect(self, websocket: WebSocket):
        """Accept and register a new connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        self.logger.info(f"Client connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a disconnected client"""
        self.active_connections.discard(websocket)
        self.logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            return
        
        disconnected = set()
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                self.logger.error(f"Error sending message: {e}")
                disconnected.add(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
    
    async def send_personal(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send message to a specific client"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            self.logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)
    
    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)


class SentimentStreamManager:
    """Manages sentiment streaming to WebSocket clients"""
    
    def __init__(self, token_list: list):
        self.token_list = token_list
        self.connection_manager = ConnectionManager()
        self.sentiment_pipeline: SentimentPipeline = None
        self.streaming = False
        self.logger = logger.bind(component="SentimentStreamManager")
    
    async def initialize(self, sentiment_pipeline: SentimentPipeline):
        """Initialize with sentiment pipeline"""
        self.sentiment_pipeline = sentiment_pipeline
        self.logger.info("SentimentStreamManager initialized")
    
    async def handle_connection(self, websocket: WebSocket):
        """Handle a new WebSocket connection"""
        await self.connection_manager.connect(websocket)
        
        try:
            # Send initial connection message
            await self.connection_manager.send_personal(
                websocket,
                {
                    "type": "connection",
                    "status": "connected",
                    "timestamp": datetime.now().isoformat(),
                    "tokens": self.token_list,
                    "message": "Connected to sentiment stream",
                }
            )
            
            # Keep connection alive
            while True:
                # Receive and handle client messages
                data = await websocket.receive_text()
                await self._handle_client_message(websocket, data)
        
        except WebSocketDisconnect:
            self.connection_manager.disconnect(websocket)
            self.logger.info("WebSocket disconnected")
        except Exception as e:
            self.logger.error(f"WebSocket error: {e}")
            self.connection_manager.disconnect(websocket)
    
    async def _handle_client_message(self, websocket: WebSocket, data: str):
        """Handle incoming client messages"""
        try:
            message = json.loads(data)
            message_type = message.get("type")
            
            if message_type == "ping":
                # Respond to ping
                await self.connection_manager.send_personal(
                    websocket,
                    {
                        "type": "pong",
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            
            elif message_type == "request_sentiment":
                # Send current sentiment
                tokens = message.get("tokens", self.token_list)
                await self._send_sentiment(websocket, tokens)
            
            elif message_type == "subscribe":
                # Subscribe to specific tokens
                tokens = message.get("tokens", self.token_list)
                await self.connection_manager.send_personal(
                    websocket,
                    {
                        "type": "subscribed",
                        "tokens": tokens,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            
            else:
                self.logger.warning(f"Unknown message type: {message_type}")
        
        except json.JSONDecodeError:
            self.logger.error("Invalid JSON received")
        except Exception as e:
            self.logger.error(f"Error handling client message: {e}")
    
    async def _send_sentiment(self, websocket: WebSocket, tokens: list):
        """Send sentiment data for specified tokens"""
        try:
            sentiments = {}
            
            for token in tokens:
                sentiment = await self.sentiment_pipeline.analyze_token(token)
                sentiments[token] = sentiment.to_dict()
            
            await self.connection_manager.send_personal(
                websocket,
                {
                    "type": "sentiment",
                    "timestamp": datetime.now().isoformat(),
                    "data": sentiments,
                }
            )
        except Exception as e:
            self.logger.error(f"Error sending sentiment: {e}")
    
    async def stream_sentiment(self, interval_seconds: int = 5):
        """Continuously stream sentiment updates to all clients"""
        self.streaming = True
        self.logger.info(f"Starting sentiment stream (interval: {interval_seconds}s)")
        
        while self.streaming:
            try:
                # Analyze all tokens
                sentiments = await self.sentiment_pipeline.analyze_all_tokens()
                
                # Prepare message
                message = {
                    "type": "sentiment_update",
                    "timestamp": datetime.now().isoformat(),
                    "data": {token: sentiment.to_dict() for token, sentiment in sentiments.items()},
                    "connection_count": self.connection_manager.get_connection_count(),
                }
                
                # Broadcast to all clients
                await self.connection_manager.broadcast(message)
                
                # Wait before next update
                await asyncio.sleep(interval_seconds)
            
            except Exception as e:
                self.logger.error(f"Error in sentiment stream: {e}")
                await asyncio.sleep(5)
    
    async def stop_streaming(self):
        """Stop streaming sentiment updates"""
        self.streaming = False
        self.logger.info("Sentiment stream stopped")
    
    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return self.connection_manager.get_connection_count()


# Global instance
sentiment_stream_manager: SentimentStreamManager = None


async def initialize_websocket(sentiment_pipeline: SentimentPipeline, token_list: list):
    """Initialize WebSocket manager"""
    global sentiment_stream_manager
    
    sentiment_stream_manager = SentimentStreamManager(token_list)
    await sentiment_stream_manager.initialize(sentiment_pipeline)
    
    logger.info("WebSocket manager initialized")


async def get_stream_manager() -> SentimentStreamManager:
    """Get the global stream manager"""
    return sentiment_stream_manager
