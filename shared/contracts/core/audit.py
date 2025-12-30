"""Audit Trail contracts - timestamps and lifecycle tracking.

Per ADR-0009: All timestamps are ISO-8601 UTC (no microseconds).
Per ADR-0018#audit-trail: All lifecycle events must be logged.

This module defines the core audit trail contracts used by all tools.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator

__version__ = "0.1.0"


class LifecycleEvent(str, Enum):
    """Standard lifecycle events tracked across all tools."""

    CREATED = "created"
    UPDATED = "updated"
    LOCKED = "locked"
    UNLOCKED = "unlocked"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


class AuditTimestamp(BaseModel):
    """A single audit timestamp entry.

    Per ADR-0009: ISO-8601 UTC format, no microseconds.
    Format: YYYY-MM-DDTHH:MM:SSZ
    """

    event: LifecycleEvent
    timestamp: datetime
    actor: str = Field(
        default="system",
        description="Who triggered this event (user ID, 'system', or tool name)",
    )
    details: str | None = Field(
        None,
        description="Optional additional context for this event",
    )

    @field_validator("timestamp", mode="before")
    @classmethod
    def normalize_timestamp(cls, v: datetime | str) -> datetime:
        """Ensure timestamp is UTC and has no microseconds."""
        if isinstance(v, str):
            v = datetime.fromisoformat(v.replace("Z", "+00:00"))
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v.replace(microsecond=0)

    def to_iso8601(self) -> str:
        """Return ISO-8601 UTC string without microseconds."""
        return self.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")


class AuditTrail(BaseModel):
    """Complete audit trail for an artifact or resource.

    Provides a chronological history of all lifecycle events.
    """

    events: list[AuditTimestamp] = Field(default_factory=list)

    def add_event(
        self,
        event: LifecycleEvent,
        actor: str = "system",
        details: str | None = None,
    ) -> "AuditTrail":
        """Add a new event to the audit trail (immutable - returns new instance)."""
        new_event = AuditTimestamp(
            event=event,
            timestamp=datetime.now(timezone.utc),
            actor=actor,
            details=details,
        )
        return AuditTrail(events=[*self.events, new_event])

    @property
    def created_at(self) -> datetime | None:
        """Return the creation timestamp if exists."""
        for event in self.events:
            if event.event == LifecycleEvent.CREATED:
                return event.timestamp
        return None

    @property
    def updated_at(self) -> datetime | None:
        """Return the most recent update timestamp."""
        for event in reversed(self.events):
            if event.event in (LifecycleEvent.UPDATED, LifecycleEvent.CREATED):
                return event.timestamp
        return None

    @property
    def locked_at(self) -> datetime | None:
        """Return the most recent lock timestamp if currently locked."""
        for event in reversed(self.events):
            if event.event == LifecycleEvent.LOCKED:
                return event.timestamp
            if event.event == LifecycleEvent.UNLOCKED:
                return None
        return None


class TimestampMixin(BaseModel):
    """Mixin providing standard timestamp fields for artifacts.

    Use this mixin in artifact models to ensure consistent timestamp handling.
    """

    created_at: datetime
    updated_at: datetime | None = None
    locked_at: datetime | None = None
    unlocked_at: datetime | None = None

    @field_validator("created_at", "updated_at", "locked_at", "unlocked_at", mode="before")
    @classmethod
    def normalize_timestamps(cls, v: datetime | str | None) -> datetime | None:
        """Ensure all timestamps are UTC and have no microseconds."""
        if v is None:
            return None
        if isinstance(v, str):
            v = datetime.fromisoformat(v.replace("Z", "+00:00"))
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v.replace(microsecond=0)


def now_utc() -> datetime:
    """Return current UTC datetime without microseconds (per ADR-0009)."""
    return datetime.now(timezone.utc).replace(microsecond=0)


def to_iso8601(dt: datetime) -> str:
    """Convert datetime to ISO-8601 UTC string without microseconds."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
