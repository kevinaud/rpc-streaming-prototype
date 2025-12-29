"""Abstract repository interface for session storage."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from rpc_stream_prototype.backend.models.domain import Proposal, Session


class SessionRepository(ABC):
  """Abstract interface for session storage.

  This interface follows the Repository pattern, providing
  a clean abstraction over the underlying data storage mechanism.
  """

  @abstractmethod
  async def create_session(self) -> Session:
    """Create a new session.

    Returns:
        The newly created session.
    """
    ...

  @abstractmethod
  async def get_session(self, session_id: str) -> Session | None:
    """Get a session by its ID.

    Args:
        session_id: The unique identifier of the session.

    Returns:
        The session if found, None otherwise.
    """
    ...

  @abstractmethod
  async def add_proposal(self, session_id: str, proposal: Proposal) -> Proposal | None:
    """Add a proposal to a session.

    Args:
        session_id: The session to add the proposal to.
        proposal: The proposal to add.

    Returns:
        The added proposal if successful, None if session not found.
    """
    ...

  @abstractmethod
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
    ...
