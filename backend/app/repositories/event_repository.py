"""SQLite Event Repository for LiveSight.

Conforms to Phase 4 specifications in 02_SYSTEM_ARCHITECTURE.md,
03_WORKFLOW_AND_DATA_CONTRACTS.md, and 04_IMPLEMENTATION_PLAN.md:
- Persist domain event metadata in SQLite
- Paginated event history query by limit, before cursor, event_type, and camera_id
- Robust transaction handling and visible error logging
- Safe serialization / deserialization of event contracts
"""

from __future__ import annotations
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import sqlite3
import threading
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from backend.app.schemas.event import BoundingBoxDict, EventResponse
from rules.schemas import DomainEvent

logger = logging.getLogger("livesight.repository")


class DatabaseError(RuntimeError):
    """Raised when a database query or transaction fails."""
    pass


class EventRepository:
    """Thread-safe SQLite repository for domain event persistence and retrieval."""

    def __init__(self, database_path: Union[str, Path] = "data/events.db") -> None:
        self.is_memory = str(database_path) == ":memory:"
        if self.is_memory:
            self.database_path = ":memory:"
        else:
            p = Path(database_path).expanduser()
            if not p.is_absolute():
                p = (Path.cwd() / p).resolve()
            p.parent.mkdir(parents=True, exist_ok=True)
            self.database_path = str(p)

        self._lock = threading.Lock()
        self._conn = sqlite3.connect(
            self.database_path,
            timeout=30.0,
            check_same_thread=False,
            isolation_level=None,  # Autocommit mode; transactions handled explicitly
        )
        self._conn.row_factory = sqlite3.Row
        if not self.is_memory:
            self._conn.execute("PRAGMA journal_mode = WAL;")
        self._conn.execute("PRAGMA foreign_keys = ON;")
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Return the configured SQLite connection."""
        return self._conn

    def close(self) -> None:
        """Close the underlying SQLite connection."""
        with self._lock:
            try:
                self._conn.close()
            except Exception:
                pass

    def _init_db(self) -> None:
        """Initialize events table and performance indexes."""
        try:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS events (
                        event_id TEXT PRIMARY KEY,
                        camera_id TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        occurred_at TEXT NOT NULL,
                        object_class TEXT NOT NULL,
                        track_id TEXT,
                        confidence REAL NOT NULL,
                        zone_id TEXT NOT NULL,
                        bbox_x1 REAL,
                        bbox_y1 REAL,
                        bbox_x2 REAL,
                        bbox_y2 REAL,
                        snapshot_path TEXT,
                        created_at TEXT NOT NULL
                    );
                    """
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_events_occurred_at ON events(occurred_at);"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_events_camera_id ON events(camera_id);"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_events_event_type ON events(event_type);"
                )
                logger.info("Initialized events repository schema at: %s", self.database_path)
        except sqlite3.Error as err:
            logger.error("Failed to initialize SQLite database '%s': %s", self.database_path, err)
            raise DatabaseError(f"Database initialization failure: {err}") from err

    def save(
        self,
        event: Union[DomainEvent, EventResponse, Dict[str, Any]],
    ) -> EventResponse:
        """Persist a single domain event into SQLite.

        Args:
            event: DomainEvent instance, EventResponse, or dictionary matching the contract.

        Returns:
            EventResponse representing the persisted record.

        Raises:
            DatabaseError: If insertion fails.
        """
        parsed = self._normalize_to_response(event)
        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        bx1 = parsed.bbox.x1 if parsed.bbox else None
        by1 = parsed.bbox.y1 if parsed.bbox else None
        bx2 = parsed.bbox.x2 if parsed.bbox else None
        by2 = parsed.bbox.y2 if parsed.bbox else None

        sql = """
        INSERT OR IGNORE INTO events (
            event_id, camera_id, event_type, occurred_at, object_class,
            track_id, confidence, zone_id, bbox_x1, bbox_y1, bbox_x2, bbox_y2,
            snapshot_path, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """

        with self._lock:
            try:
                with self._get_connection() as conn:
                    conn.execute(
                        sql,
                        (
                            parsed.event_id,
                            parsed.camera_id,
                            parsed.event_type,
                            parsed.occurred_at,
                            parsed.object_class,
                            str(parsed.track_id) if parsed.track_id is not None else None,
                            float(parsed.confidence),
                            parsed.zone_id,
                            bx1,
                            by1,
                            bx2,
                            by2,
                            parsed.snapshot_path,
                            now_utc,
                        ),
                    )
            except sqlite3.Error as err:
                logger.error("Database write failed for event '%s': %s", parsed.event_id, err)
                raise DatabaseError(f"Failed to persist event {parsed.event_id}: {err}") from err

        return parsed

    def save_many(
        self,
        events: Sequence[Union[DomainEvent, EventResponse, Dict[str, Any]]],
    ) -> List[EventResponse]:
        """Persist multiple domain events in a single transaction."""
        if not events:
            return []

        results: List[EventResponse] = []
        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        rows = []
        for e in events:
            parsed = self._normalize_to_response(e)
            results.append(parsed)
            bx1 = parsed.bbox.x1 if parsed.bbox else None
            by1 = parsed.bbox.y1 if parsed.bbox else None
            bx2 = parsed.bbox.x2 if parsed.bbox else None
            by2 = parsed.bbox.y2 if parsed.bbox else None
            rows.append(
                (
                    parsed.event_id,
                    parsed.camera_id,
                    parsed.event_type,
                    parsed.occurred_at,
                    parsed.object_class,
                    str(parsed.track_id) if parsed.track_id is not None else None,
                    float(parsed.confidence),
                    parsed.zone_id,
                    bx1,
                    by1,
                    bx2,
                    by2,
                    parsed.snapshot_path,
                    now_utc,
                )
            )

        sql = """
        INSERT OR IGNORE INTO events (
            event_id, camera_id, event_type, occurred_at, object_class,
            track_id, confidence, zone_id, bbox_x1, bbox_y1, bbox_x2, bbox_y2,
            snapshot_path, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """

        with self._lock:
            try:
                with self._get_connection() as conn:
                    conn.executemany(sql, rows)
            except sqlite3.Error as err:
                logger.error("Database batch write failed for %d events: %s", len(rows), err)
                raise DatabaseError(f"Failed to persist batch events: {err}") from err

        return results

    def get_by_id(self, event_id: str) -> Optional[EventResponse]:
        """Retrieve an event by unique event_id."""
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.execute(
                        "SELECT * FROM events WHERE event_id = ? LIMIT 1;", (event_id,)
                    )
                    row = cursor.fetchone()
                    if row is None:
                        return None
                    return self._row_to_response(row)
            except sqlite3.Error as err:
                logger.error("Database query failed for event '%s': %s", event_id, err)
                raise DatabaseError(f"Failed to query event {event_id}: {err}") from err

    def list_events(
        self,
        limit: int = 50,
        before: Optional[str] = None,
        event_type: Optional[str] = None,
        camera_id: Optional[str] = None,
    ) -> Tuple[List[EventResponse], Optional[str]]:
        """Query event history ordered by occurred_at DESC with pagination cursor.

        Args:
            limit: Maximum items to return (1..100).
            before: ISO-8601 timestamp cursor; returns events that occurred before this time.
            event_type: Optional event_type filter.
            camera_id: Optional camera_id filter.

        Returns:
            Tuple of (list_of_items, next_cursor).
        """
        if limit < 1 or limit > 100:
            raise ValueError(f"limit must be between 1 and 100, got {limit}")

        query = ["SELECT * FROM events WHERE 1=1"]
        params: List[Any] = []

        if before:
            query.append("AND occurred_at < ?")
            params.append(before)

        if event_type:
            query.append("AND event_type = ?")
            params.append(event_type)

        if camera_id:
            query.append("AND camera_id = ?")
            params.append(camera_id)

        # Retrieve limit + 1 to check if there is a next page
        query.append("ORDER BY occurred_at DESC, event_id DESC LIMIT ?;")
        params.append(limit + 1)

        sql = " ".join(query)

        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.execute(sql, params)
                    rows = cursor.fetchall()
            except sqlite3.Error as err:
                logger.error("Database query failed in list_events: %s", err)
                raise DatabaseError(f"Failed to query events: {err}") from err

        items = [self._row_to_response(r) for r in rows[:limit]]

        next_cursor: Optional[str] = None
        if len(rows) > limit:
            # The next cursor is the occurred_at of the last item in this page
            next_cursor = items[-1].occurred_at

        return items, next_cursor

    def count(
        self,
        event_type: Optional[str] = None,
        camera_id: Optional[str] = None,
    ) -> int:
        """Count total persisted events matching optional filters."""
        query = ["SELECT COUNT(*) AS total FROM events WHERE 1=1"]
        params: List[Any] = []

        if event_type:
            query.append("AND event_type = ?")
            params.append(event_type)

        if camera_id:
            query.append("AND camera_id = ?")
            params.append(camera_id)

        sql = " ".join(query)

        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.execute(sql, params)
                    row = cursor.fetchone()
                    return int(row["total"]) if row else 0
            except sqlite3.Error as err:
                logger.error("Database count failed: %s", err)
                raise DatabaseError(f"Failed to count events: {err}") from err

    def clear(self) -> None:
        """Delete all events (for test fixture teardown)."""
        with self._lock:
            try:
                with self._get_connection() as conn:
                    conn.execute("DELETE FROM events;")
            except sqlite3.Error as err:
                logger.error("Database clear failed: %s", err)
                raise DatabaseError(f"Failed to clear events: {err}") from err

    @staticmethod
    def _normalize_to_response(
        event: Union[DomainEvent, EventResponse, Dict[str, Any]],
    ) -> EventResponse:
        """Convert any supported event representation to validated EventResponse."""
        if isinstance(event, EventResponse):
            return event

        if isinstance(event, DomainEvent):
            data = event.to_dict()
        elif isinstance(event, dict):
            data = dict(event)
        else:
            raise TypeError(f"Unsupported event type: {type(event)}")

        bbox_raw = data.get("bbox")
        bbox_dict = None
        if bbox_raw and isinstance(bbox_raw, dict):
            bbox_dict = BoundingBoxDict(
                x1=float(bbox_raw["x1"]),
                y1=float(bbox_raw["y1"]),
                x2=float(bbox_raw["x2"]),
                y2=float(bbox_raw["y2"]),
            )

        return EventResponse(
            event_id=str(data["event_id"]),
            camera_id=str(data["camera_id"]),
            event_type=str(data["event_type"]),
            occurred_at=str(data["occurred_at"]),
            object_class=str(data["object_class"]),
            track_id=str(data["track_id"]) if data.get("track_id") is not None else None,
            confidence=round(float(data["confidence"]), 4),
            zone_id=str(data["zone_id"]),
            bbox=bbox_dict,
            snapshot_path=data.get("snapshot_path"),
        )

    @staticmethod
    def _row_to_response(row: sqlite3.Row) -> EventResponse:
        """Convert a database row into an EventResponse."""
        bbox_dict = None
        if (
            row["bbox_x1"] is not None
            and row["bbox_y1"] is not None
            and row["bbox_x2"] is not None
            and row["bbox_y2"] is not None
        ):
            bbox_dict = BoundingBoxDict(
                x1=float(row["bbox_x1"]),
                y1=float(row["bbox_y1"]),
                x2=float(row["bbox_x2"]),
                y2=float(row["bbox_y2"]),
            )

        return EventResponse(
            event_id=row["event_id"],
            camera_id=row["camera_id"],
            event_type=row["event_type"],
            occurred_at=row["occurred_at"],
            object_class=row["object_class"],
            track_id=row["track_id"],
            confidence=float(row["confidence"]),
            zone_id=row["zone_id"],
            bbox=bbox_dict,
            snapshot_path=row["snapshot_path"],
        )
