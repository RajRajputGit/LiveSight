"""Application Event Service coordinating persistence and real-time broadcasting.

Conforms to Phase 4 specifications in 02_SYSTEM_ARCHITECTURE.md and 03_WORKFLOW_AND_DATA_CONTRACTS.md.
"""

from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional, Union

from backend.app.repositories.event_repository import EventRepository
from backend.app.schemas.event import EventListResponse, EventResponse
from backend.app.services.event_publisher import EventPublisher
from rules.schemas import DomainEvent

logger = logging.getLogger("livesight.event_service")


class EventService:
    """Coordinates event persistence in SQLite and real-time publishing to WebSocket clients."""

    def __init__(
        self,
        repository: EventRepository,
        publisher: EventPublisher,
    ) -> None:
        self.repository = repository
        self.publisher = publisher

    def record_event(
        self,
        event: Union[DomainEvent, EventResponse, Dict[str, Any]],
    ) -> EventResponse:
        """Persist a newly detected domain event and broadcast it to live subscribers."""
        persisted = self.repository.save(event)

        # Broadcast to WebSocket subscribers (thread-safe bridge)
        try:
            self.publisher.publish_from_thread(persisted)
        except Exception as exc:
            logger.warning("Failed to dispatch live event to publisher: %s", exc)

        return persisted

    def get_events(
        self,
        limit: int = 50,
        before: Optional[str] = None,
        event_type: Optional[str] = None,
        camera_id: Optional[str] = None,
    ) -> EventListResponse:
        """Retrieve paginated events from SQLite repository."""
        items, next_cursor = self.repository.list_events(
            limit=limit,
            before=before,
            event_type=event_type,
            camera_id=camera_id,
        )
        return EventListResponse(items=items, next_cursor=next_cursor)

    def get_event_by_id(self, event_id: str) -> Optional[EventResponse]:
        """Fetch a single event by unique ID."""
        return self.repository.get_by_id(event_id)
