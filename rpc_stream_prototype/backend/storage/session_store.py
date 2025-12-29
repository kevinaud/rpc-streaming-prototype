"""Session store abstraction combining storage and pub/sub.

This module provides a unified abstraction that wraps in-memory storage
with pub/sub functionality, ensuring atomic operations and consistent
event broadcasting.
"""

import asyncio
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from rpc_stream_prototype.backend.events.proto_broadcaster import ProtoBroadcaster
from rpc_stream_prototype.generated.proposal.v1 import (
  Proposal,
  ProposalStatus,
  Session,
  SessionEvent,
)

if TYPE_CHECKING:
  from collections.abc import AsyncIterator


@dataclass
class SessionData:
  """Internal session data container.

  Stores proposals in-memory with their ordering.
  """

  session_id: str
  proposals: list[Proposal]
  created_at: datetime


class SessionStore:
  """Unified session storage with integrated pub/sub.

  This class wraps in-memory storage and broadcaster together to ensure
  that updates to storage and event broadcasts are consistently coordinated.
  The pattern is: update storage first (source of truth), then broadcast.

  Example:
      >>> store = SessionStore()
      >>> await store.connect()
      >>> session = await store.create_session()
      >>> proposal = await store.add_proposal(session.session_id, "My proposal")
      >>> async for event in store.watch_session(session.session_id):
      ...     print(event)
  """

  def __init__(self, broadcast_url: str = "memory://") -> None:
    """Initialize the store with empty storage and broadcaster.

    Args:
        broadcast_url: The broadcaster backend URL (default: in-memory).
    """
    self._sessions: dict[str, SessionData] = {}
    self._lock = asyncio.Lock()
    self._broadcaster: ProtoBroadcaster[SessionEvent] = ProtoBroadcaster(
      broadcast_url, SessionEvent
    )

  async def connect(self) -> None:
    """Connect to the broadcast backend."""
    await self._broadcaster.connect()

  async def disconnect(self) -> None:
    """Disconnect from the broadcast backend."""
    await self._broadcaster.disconnect()

  def _channel_for_session(self, session_id: str) -> str:
    """Get the broadcast channel name for a session.

    Args:
        session_id: The session identifier.

    Returns:
        The channel name for pub/sub routing.
    """
    return f"session:{session_id}"

  async def create_session(self) -> Session:
    """Create a new session.

    Returns:
        The newly created session proto.
    """
    session_id = str(uuid.uuid4())
    session_data = SessionData(
      session_id=session_id,
      proposals=[],
      created_at=datetime.now(UTC),
    )

    async with self._lock:
      self._sessions[session_id] = session_data

    return Session(session_id=session_id)

  async def get_session(self, session_id: str) -> Session | None:
    """Get a session by its ID.

    Args:
        session_id: The unique identifier of the session.

    Returns:
        The session proto if found, None otherwise.
    """
    async with self._lock:
      session_data = self._sessions.get(session_id)
      if session_data is None:
        return None
      return Session(session_id=session_data.session_id)

  async def session_exists(self, session_id: str) -> bool:
    """Check if a session exists.

    Args:
        session_id: The session ID to check.

    Returns:
        True if the session exists, False otherwise.
    """
    async with self._lock:
      return session_id in self._sessions

  async def add_proposal(self, session_id: str, text: str) -> Proposal | None:
    """Add a proposal to a session and broadcast the event.

    This is an atomic operation: storage is updated first, then the event
    is broadcast to all subscribers.

    Args:
        session_id: The session to add the proposal to.
        text: The text content of the proposal.

    Returns:
        The created proposal if successful, None if session not found.
    """
    proposal = Proposal(
      proposal_id=str(uuid.uuid4()),
      text=text,
      status=ProposalStatus.PENDING,
      created_at=datetime.now(UTC),
    )

    async with self._lock:
      session_data = self._sessions.get(session_id)
      if session_data is None:
        return None
      session_data.proposals.append(proposal)

    # Broadcast after releasing the lock
    event = SessionEvent(proposal_created=proposal)
    await self._broadcaster.publish(self._channel_for_session(session_id), event)

    return proposal

  async def update_proposal(
    self,
    session_id: str,
    proposal_id: str,
    *,
    approved: bool,
  ) -> Proposal | None:
    """Update a proposal's status and broadcast the event.

    This is an atomic operation: storage is updated first, then the event
    is broadcast to all subscribers.

    Args:
        session_id: The session containing the proposal.
        proposal_id: The proposal to update.
        approved: Whether to approve (True) or reject (False).

    Returns:
        The updated proposal if successful, None if not found.
    """
    new_status = ProposalStatus.APPROVED if approved else ProposalStatus.REJECTED
    updated: Proposal | None = None

    async with self._lock:
      session_data = self._sessions.get(session_id)
      if session_data is None:
        return None

      # Find and update the proposal
      for i, proposal in enumerate(session_data.proposals):
        if proposal.proposal_id == proposal_id:
          updated = Proposal(
            proposal_id=proposal.proposal_id,
            text=proposal.text,
            status=new_status,
            created_at=proposal.created_at,
          )
          session_data.proposals[i] = updated
          break

    if updated is None:
      return None

    # Broadcast after releasing the lock
    event = SessionEvent(proposal_updated=updated)
    await self._broadcaster.publish(self._channel_for_session(session_id), event)

    return updated

  async def get_proposals(self, session_id: str) -> list[Proposal]:
    """Get all proposals for a session.

    Args:
        session_id: The session to get proposals for.

    Returns:
        List of proposals, or empty list if session not found.
    """
    async with self._lock:
      session_data = self._sessions.get(session_id)
      if session_data is None:
        return []
      # Return a copy to prevent external mutation
      return list(session_data.proposals)

  async def watch_session(self, session_id: str) -> AsyncIterator[SessionEvent]:
    """Watch a session for events.

    This method combines history replay with live streaming:
    1. Subscribe FIRST to buffer any events during snapshot read
    2. Get current snapshot (history)
    3. Yield historical proposals as synthetic events
    4. Yield live updates from the subscription

    This prevents the race condition where events fire while reading history.

    Args:
        session_id: The session to watch.

    Yields:
        SessionEvent protos for both historical and live events.
    """
    channel = self._channel_for_session(session_id)

    async with self._broadcaster.subscribe(channel) as stream:
      # A. Subscription is now active, buffering any events

      # B. Get snapshot (history)
      current_proposals = await self.get_proposals(session_id)

      # C. Yield snapshot as synthetic events
      for proposal in current_proposals:
        if proposal.status == ProposalStatus.PENDING:
          yield SessionEvent(proposal_created=proposal)
        else:
          yield SessionEvent(proposal_updated=proposal)

      # D. Yield live updates
      async for event in stream:
        yield event
