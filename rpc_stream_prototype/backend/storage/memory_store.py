"""In-memory implementation of the session repository."""

import asyncio
from typing import TYPE_CHECKING

from rpc_stream_prototype.backend.models.domain import Session
from rpc_stream_prototype.backend.storage.repository import SessionRepository

if TYPE_CHECKING:
  from rpc_stream_prototype.backend.models.domain import Proposal


class InMemorySessionRepository(SessionRepository):
  """Thread-safe in-memory session repository.

  This implementation stores sessions in a dictionary and uses
  an asyncio.Lock to ensure thread-safe access.
  """

  def __init__(self) -> None:
    """Initialize the repository with empty storage."""
    self._sessions: dict[str, Session] = {}
    self._lock = asyncio.Lock()

  async def create_session(self) -> Session:
    """Create a new session.

    Returns:
        The newly created session.
    """
    session = Session.create()
    async with self._lock:
      self._sessions[session.session_id] = session
    return session

  async def get_session(self, session_id: str) -> Session | None:
    """Get a session by its ID.

    Args:
        session_id: The unique identifier of the session.

    Returns:
        The session if found, None otherwise.
    """
    async with self._lock:
      return self._sessions.get(session_id)

  async def add_proposal(self, session_id: str, proposal: Proposal) -> Proposal | None:
    """Add a proposal to a session.

    Args:
        session_id: The session to add the proposal to.
        proposal: The proposal to add.

    Returns:
        The added proposal if successful, None if session not found.
    """
    async with self._lock:
      session = self._sessions.get(session_id)
      if session is None:
        return None
      session.add_proposal(proposal)
      return proposal

  async def update_proposal(
    self, session_id: str, proposal_id: str, *, approved: bool
  ) -> Proposal | None:
    """Update a proposal's status.

    Args:
        session_id: The session containing the proposal.
        proposal_id: The proposal to update.
        approved: Whether to approve (True) or reject (False).

    Returns:
        The updated proposal if successful, None if not found.
    """
    async with self._lock:
      session = self._sessions.get(session_id)
      if session is None:
        return None

      proposal = session.get_proposal(proposal_id)
      if proposal is None:
        return None

      updated = proposal.approve() if approved else proposal.reject()
      session.update_proposal(updated)
      return updated
