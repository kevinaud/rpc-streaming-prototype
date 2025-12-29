"""Fake ProposalClient for CLI unit tests.

This fake provides canned responses for testing CLI components
without making real network calls. It follows the Classicist testing
approach by being state-verifiable.
"""

from typing import TYPE_CHECKING

from rpc_stream_prototype.generated.proposal.v1 import (
  Proposal,
  ProposalStatus,
  SessionEvent,
)

if TYPE_CHECKING:
  from collections.abc import AsyncIterator


class FakeProposalClient:
  """Fake gRPC client for testing CLI components.

  This fake:
  - Records method calls for verification
  - Allows configuring responses
  - Provides async context manager support
  """

  def __init__(self) -> None:
    """Initialize the fake client."""
    self.connected = False
    self.closed = False

    # Configurable responses
    self.session_id: str = "test-session-123"
    self.session_exists: bool = True
    self.proposals: list[Proposal] = []
    self.events_to_yield: list[SessionEvent] = []

    # Call tracking
    self.create_session_calls: int = 0
    self.get_session_calls: list[str] = []
    self.submit_proposal_calls: list[tuple[str, str]] = []
    self.subscribe_calls: list[tuple[str, str]] = []

  async def connect(self) -> None:
    """Simulate connection."""
    self.connected = True

  async def close(self) -> None:
    """Simulate closing connection."""
    self.closed = True
    self.connected = False

  async def __aenter__(self) -> FakeProposalClient:
    """Async context manager entry."""
    await self.connect()
    return self

  async def __aexit__(self, *args: object) -> None:
    """Async context manager exit."""
    await self.close()

  async def session(self) -> AsyncIterator[FakeProposalClient]:
    """Yield self as async context manager for session() compatibility."""
    await self.connect()
    try:
      yield self
    finally:
      await self.close()

  async def create_session(self) -> str:
    """Return a fake session ID."""
    self.create_session_calls += 1
    return self.session_id

  async def get_session(self, session_id: str) -> bool:
    """Return whether the session exists."""
    self.get_session_calls.append(session_id)
    return self.session_exists

  async def submit_proposal(self, session_id: str, text: str) -> Proposal:
    """Return a fake proposal."""
    self.submit_proposal_calls.append((session_id, text))
    proposal = Proposal(
      proposal_id=f"proposal-{len(self.submit_proposal_calls)}",
      text=text,
      status=ProposalStatus.PENDING,
    )
    self.proposals.append(proposal)
    return proposal

  async def subscribe(
    self, session_id: str, client_id: str
  ) -> AsyncIterator[SessionEvent]:
    """Yield configured events."""
    self.subscribe_calls.append((session_id, client_id))
    for event in self.events_to_yield:
      yield event

  def configure_decision(self, proposal_id: str, approved: bool) -> None:
    """Add a decision event to be yielded by subscribe().

    Args:
      proposal_id: The proposal ID to decide on.
      approved: Whether the proposal is approved.
    """
    status = ProposalStatus.APPROVED if approved else ProposalStatus.REJECTED
    event = SessionEvent(
      proposal_updated=Proposal(
        proposal_id=proposal_id,
        text="test proposal",
        status=status,
      )
    )
    self.events_to_yield.append(event)
