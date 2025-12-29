"""Fake ProposalServiceStub for CLI unit tests.

This fake provides canned responses for testing CLI components
without making real network calls. It follows the Classicist testing
approach by being state-verifiable.
"""

from typing import TYPE_CHECKING

from rpc_stream_prototype.generated.proposal.v1 import (
  CreateSessionResponse,
  GetSessionResponse,
  Proposal,
  ProposalStatus,
  Session,
  SessionEvent,
  SubmitProposalResponse,
  SubscribeResponse,
)

if TYPE_CHECKING:
  from collections.abc import AsyncIterator

  from rpc_stream_prototype.generated.proposal.v1 import (
    CreateSessionRequest,
    GetSessionRequest,
    SubmitProposalRequest,
    SubscribeRequest,
  )


class FakeProposalServiceStub:
  """Fake gRPC stub for testing CLI components.

  This fake:
  - Records method calls for verification
  - Allows configuring responses
  - Mirrors the ProposalServiceStub interface from betterproto
  """

  def __init__(self) -> None:
    """Initialize the fake stub."""
    # Configurable responses
    self.session_id: str = "test-session-123"
    self.session_exists: bool = True
    self.proposals: list[Proposal] = []
    self.events_to_yield: list[SubscribeResponse] = []

    # Call tracking
    self.create_session_calls: int = 0
    self.get_session_calls: list[str] = []
    self.submit_proposal_calls: list[tuple[str, str]] = []
    self.subscribe_calls: list[tuple[str, str]] = []

    # Error simulation
    self.get_session_raises: Exception | None = None

  async def create_session(
    self,
    request: CreateSessionRequest,
    **kwargs: object,
  ) -> CreateSessionResponse:
    """Return a fake session."""
    self.create_session_calls += 1
    return CreateSessionResponse(
      session=Session(session_id=self.session_id),
    )

  async def get_session(
    self,
    request: GetSessionRequest,
    **kwargs: object,
  ) -> GetSessionResponse:
    """Return whether the session exists or raise."""
    self.get_session_calls.append(request.session_id)
    if self.get_session_raises:
      raise self.get_session_raises
    if not self.session_exists:
      msg = "Session not found"
      raise Exception(msg)
    return GetSessionResponse(
      session=Session(session_id=request.session_id),
    )

  async def submit_proposal(
    self,
    request: SubmitProposalRequest,
    **kwargs: object,
  ) -> SubmitProposalResponse:
    """Return a fake proposal."""
    self.submit_proposal_calls.append((request.session_id, request.text))
    proposal = Proposal(
      proposal_id=f"proposal-{len(self.submit_proposal_calls)}",
      text=request.text,
      status=ProposalStatus.PENDING,
    )
    self.proposals.append(proposal)
    return SubmitProposalResponse(proposal=proposal)

  async def subscribe(
    self,
    request: SubscribeRequest,
    **kwargs: object,
  ) -> AsyncIterator[SubscribeResponse]:
    """Yield configured events."""
    self.subscribe_calls.append((request.session_id, request.client_id))
    for response in self.events_to_yield:
      yield response

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
    self.events_to_yield.append(SubscribeResponse(event=event))


# Alias for backwards compatibility with test imports
FakeProposalClient = FakeProposalServiceStub
