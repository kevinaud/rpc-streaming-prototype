"""Event broadcaster for real-time session updates.

This module implements the publish-subscribe pattern for broadcasting
session events to connected clients.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from rpc_stream_prototype.backend.models.domain import Proposal


class EventType(Enum):
  """Types of session events."""

  PROPOSAL_CREATED = "proposal_created"
  PROPOSAL_UPDATED = "proposal_updated"


@dataclass
class SessionEvent:
  """An event that occurred in a session.

  Attributes:
      session_id: The session this event belongs to.
      event_type: The type of event.
      proposal: The proposal associated with this event.
  """

  session_id: str
  event_type: EventType
  proposal: Proposal


class EventBroadcaster:
  """Broadcasts events to subscribed clients.

  This class manages subscriptions for session events and provides
  thread-safe broadcasting of events to all subscribers.

  Example:
      >>> broadcaster = EventBroadcaster()
      >>> queue = await broadcaster.subscribe("session-123")
      >>> # In another coroutine:
      >>> await broadcaster.broadcast(event)
      >>> # The queue will receive the event
  """

  def __init__(self) -> None:
    """Initialize the broadcaster with empty subscriptions."""
    self._subscribers: dict[str, set[asyncio.Queue[SessionEvent]]] = {}
    self._lock = asyncio.Lock()

  async def subscribe(self, session_id: str) -> asyncio.Queue[SessionEvent]:
    """Subscribe to events for a session.

    Args:
        session_id: The session to subscribe to.

    Returns:
        A queue that will receive events for this session.
    """
    queue: asyncio.Queue[SessionEvent] = asyncio.Queue()
    async with self._lock:
      if session_id not in self._subscribers:
        self._subscribers[session_id] = set()
      self._subscribers[session_id].add(queue)
    return queue

  async def unsubscribe(
    self, session_id: str, queue: asyncio.Queue[SessionEvent]
  ) -> None:
    """Unsubscribe from session events.

    Args:
        session_id: The session to unsubscribe from.
        queue: The queue to remove from subscriptions.
    """
    async with self._lock:
      if session_id in self._subscribers:
        self._subscribers[session_id].discard(queue)
        # Clean up empty subscription sets
        if not self._subscribers[session_id]:
          del self._subscribers[session_id]

  async def broadcast(self, event: SessionEvent) -> None:
    """Broadcast an event to all subscribers of the session.

    Args:
        event: The event to broadcast.
    """
    async with self._lock:
      subscribers = self._subscribers.get(event.session_id, set()).copy()

    # Broadcast outside the lock to avoid blocking
    for queue in subscribers:
      try:
        queue.put_nowait(event)
      except asyncio.QueueFull:
        # If a subscriber's queue is full, skip it
        # This prevents slow consumers from blocking others
        pass

  async def get_subscriber_count(self, session_id: str) -> int:
    """Get the number of subscribers for a session.

    Args:
        session_id: The session to check.

    Returns:
        The number of active subscribers.
    """
    async with self._lock:
      return len(self._subscribers.get(session_id, set()))
