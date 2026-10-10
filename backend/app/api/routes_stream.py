"""Live WebSocket stream router for real-time domain event broadcasting.

Conforms to Section 5 of 05_API_SPECIFICATION.md.
"""

from __future__ import annotations
import logging
from starlette.websockets import WebSocket, WebSocketDisconnect
from fastapi import APIRouter

logger = logging.getLogger("livesight.stream")

router = APIRouter(tags=["Live Stream"])


@router.websocket("/events/stream")
async def websocket_event_stream(websocket: WebSocket) -> None:
    """Stream live domain events to connected WebSocket subscribers."""
    publisher = getattr(websocket.app.state, "event_publisher", None)

    if publisher is None:
        await websocket.close(code=1011, reason="Publisher service unavailable")
        return

    await publisher.connect(websocket)

    try:
        while True:
            # Maintain active connection; accept client pings/messages
            data = await websocket.receive_text()
            logger.debug("Received ping from WebSocket client: %s", data)
    except WebSocketDisconnect:
        logger.info("WebSocket subscriber disconnected normally.")
    except Exception as exc:
        logger.warning("WebSocket subscriber closed with exception: %s", exc)
    finally:
        await publisher.disconnect(websocket)
