"""WebSocket Event Publisher for live event streaming.

Conforms to Phase 4 specifications in 02_SYSTEM_ARCHITECTURE.md and 05_API_SPECIFICATION.md:
- Broadcasts new domain events to connected WebSocket subscribers
- Payload contract: {"type": "event.created", "data": {...}}
- Handles client disconnects cleanly without crashing publisher or interrupting other clients
- Supports thread-safe publishing from background vision threads
"""

from __future__ import annotations
import asyncio
import json
import logging
import threading
from typing import Any, Dict, Optional, Set, Union
from starlette.websockets import WebSocket, WebSocketState

from backend.app.schemas.event import EventResponse, EventStreamMessage

logger = logging.getLogger("livesight.publisher")


class EventPublisher:
    """Thread-safe WebSocket manager broadcasting domain events to connected subscribers."""

    def __init__(self) -> None:
        self._active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock() if hasattr(asyncio, "Lock") else None
        self._sync_lock = threading.Lock()
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def set_event_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Register the running asyncio event loop for thread-safe cross-thread dispatch."""
        self._loop = loop

    @property
    def client_count(self) -> int:
        """Number of active WebSocket subscriber connections."""
        with self._sync_lock:
            return len(self._active_connections)

    async def connect(self, websocket: WebSocket) -> None:
        """Register a newly accepted WebSocket connection."""
        await websocket.accept()
        with self._sync_lock:
            self._active_connections.add(websocket)
        logger.info(
            "WebSocket client connected. Active subscribers: %d",
            len(self._active_connections),
        )

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a disconnected WebSocket client."""
        with self._sync_lock:
            self._active_connections.discard(websocket)
        logger.info(
            "WebSocket client disconnected. Active subscribers: %d",
            len(self._active_connections),
        )

    async def broadcast(self, event: Union[EventResponse, Dict[str, Any]]) -> None:
        """Broadcast a domain event payload to all active subscribers.

        Ensures that client disconnects or network write errors do not crash the publisher.
        """
        if isinstance(event, EventResponse):
            payload_data = event.model_dump()
        elif hasattr(event, "to_dict"):
            payload_data = event.to_dict()
        else:
            payload_data = dict(event)

        message = {
            "type": "event.created",
            "data": payload_data,
        }
        message_json = json.dumps(message)

        with self._sync_lock:
            connections = list(self._active_connections)

        if not connections:
            return

        dead_connections: Set[WebSocket] = set()

        for ws in connections:
            try:
                if ws.client_state == WebSocketState.CONNECTED:
                    await ws.send_text(message_json)
                else:
                    dead_connections.add(ws)
            except Exception as exc:
                logger.warning("Failed to send message to WebSocket client: %s", exc)
                dead_connections.add(ws)

        if dead_connections:
            with self._sync_lock:
                for ws in dead_connections:
                    self._active_connections.discard(ws)
            logger.debug(
                "Cleaned up %d disconnected WebSocket clients. Remaining: %d",
                len(dead_connections),
                len(self._active_connections),
            )

    def publish_from_thread(self, event: Union[EventResponse, Dict[str, Any]]) -> None:
        """Thread-safe synchronous bridge for background worker threads to broadcast events."""
        if self._loop is not None and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(self.broadcast(event), self._loop)
        else:
            logger.debug("No active event loop available to broadcast event from thread.")
