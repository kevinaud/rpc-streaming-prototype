"""Unit tests for the ProposalService."""

import asyncio
from typing import TYPE_CHECKING

import grpclib
import pytest

from rpc_stream_prototype.backend.events.broadcaster import EventBroadcaster, EventType
from rpc_stream_prototype.backend.services.proposal_service import ProposalService
from rpc_stream_prototype.backend.storage.memory_store import InMemorySessionRepository
from rpc_stream_prototype.generated.proposal.v1 import (
  CreateSessionRequest,
  GetSessionRequest,
  ProposalStatus,
  SubmitDecisionRequest,
  SubmitProposalRequest,
  SubscribeRequest,
)

if TYPE_CHECKING:
  from rpc_stream_prototype.generated.proposal.v1 import SessionEvent


class TestProposalService:
  """Tests for ProposalService."""

  @pytest.fixture
  def repository(self) -> InMemorySessionRepository:
    """Create a fresh repository for each test."""
    return InMemorySessionRepository()

  @pytest.fixture
  def broadcaster(self) -> EventBroadcaster:
    """Create a fresh broadcaster for each test."""
    return EventBroadcaster()

  @pytest.fixture
  def service(
    self,
    repository: InMemorySessionRepository,
    broadcaster: EventBroadcaster,
  ) -> ProposalService:
    """Create a service with fresh dependencies."""
    return ProposalService(repository, broadcaster)


class TestCreateSession(TestProposalService):
  """Tests for CreateSession RPC."""

  @pytest.mark.asyncio
  async def test_returns_session_with_id(self, service: ProposalService) -> None:
    """CreateSession returns a session with a valid UUID."""
    request = CreateSessionRequest()

    response = await service.create_session(request)

    assert response.session is not None
    assert len(response.session.session_id) == 36  # UUID format

  @pytest.mark.asyncio
  async def test_creates_unique_sessions(self, service: ProposalService) -> None:
    """CreateSession creates unique session IDs."""
    request = CreateSessionRequest()

    response1 = await service.create_session(request)
    response2 = await service.create_session(request)

    assert response1.session.session_id != response2.session.session_id

  @pytest.mark.asyncio
  async def test_session_is_persisted(
    self,
    service: ProposalService,
    repository: InMemorySessionRepository,
  ) -> None:
    """CreateSession persists the session in the repository."""
    request = CreateSessionRequest()

    response = await service.create_session(request)

    session = await repository.get_session(response.session.session_id)
    assert session is not None


class TestGetSession(TestProposalService):
  """Tests for GetSession RPC."""

  @pytest.mark.asyncio
  async def test_returns_existing_session(self, service: ProposalService) -> None:
    """GetSession returns an existing session."""
    create_response = await service.create_session(CreateSessionRequest())
    session_id = create_response.session.session_id

    request = GetSessionRequest(session_id=session_id)
    response = await service.get_session(request)

    assert response.session.session_id == session_id

  @pytest.mark.asyncio
  async def test_raises_not_found_for_nonexistent(
    self, service: ProposalService
  ) -> None:
    """GetSession raises NOT_FOUND for nonexistent session."""
    request = GetSessionRequest(session_id="nonexistent-id")

    with pytest.raises(grpclib.GRPCError) as exc_info:
      await service.get_session(request)

    assert exc_info.value.status == grpclib.const.Status.NOT_FOUND


class TestSubmitProposal(TestProposalService):
  """Tests for SubmitProposal RPC."""

  @pytest.mark.asyncio
  async def test_returns_created_proposal(self, service: ProposalService) -> None:
    """SubmitProposal returns the created proposal."""
    session = await service.create_session(CreateSessionRequest())
    request = SubmitProposalRequest(
      session_id=session.session.session_id,
      text="Test proposal",
    )

    response = await service.submit_proposal(request)

    assert response.proposal is not None
    assert response.proposal.text == "Test proposal"
    assert response.proposal.status == ProposalStatus.PENDING

  @pytest.mark.asyncio
  async def test_generates_proposal_id(self, service: ProposalService) -> None:
    """SubmitProposal generates a unique proposal ID."""
    session = await service.create_session(CreateSessionRequest())
    request = SubmitProposalRequest(
      session_id=session.session.session_id,
      text="Test proposal",
    )

    response = await service.submit_proposal(request)

    assert len(response.proposal.proposal_id) == 36  # UUID format

  @pytest.mark.asyncio
  async def test_raises_not_found_for_nonexistent_session(
    self, service: ProposalService
  ) -> None:
    """SubmitProposal raises NOT_FOUND for nonexistent session."""
    request = SubmitProposalRequest(
      session_id="nonexistent",
      text="Test proposal",
    )

    with pytest.raises(grpclib.GRPCError) as exc_info:
      await service.submit_proposal(request)

    assert exc_info.value.status == grpclib.const.Status.NOT_FOUND

  @pytest.mark.asyncio
  async def test_raises_invalid_argument_for_empty_text(
    self, service: ProposalService
  ) -> None:
    """SubmitProposal raises INVALID_ARGUMENT for empty text."""
    session = await service.create_session(CreateSessionRequest())
    request = SubmitProposalRequest(
      session_id=session.session.session_id,
      text="",
    )

    with pytest.raises(grpclib.GRPCError) as exc_info:
      await service.submit_proposal(request)

    assert exc_info.value.status == grpclib.const.Status.INVALID_ARGUMENT

  @pytest.mark.asyncio
  async def test_raises_invalid_argument_for_whitespace_only(
    self, service: ProposalService
  ) -> None:
    """SubmitProposal raises INVALID_ARGUMENT for whitespace-only text."""
    session = await service.create_session(CreateSessionRequest())
    request = SubmitProposalRequest(
      session_id=session.session.session_id,
      text="   ",
    )

    with pytest.raises(grpclib.GRPCError) as exc_info:
      await service.submit_proposal(request)

    assert exc_info.value.status == grpclib.const.Status.INVALID_ARGUMENT

  @pytest.mark.asyncio
  async def test_broadcasts_proposal_created_event(
    self,
    service: ProposalService,
    broadcaster: EventBroadcaster,
  ) -> None:
    """SubmitProposal broadcasts a PROPOSAL_CREATED event."""
    session = await service.create_session(CreateSessionRequest())
    session_id = session.session.session_id

    # Subscribe before submitting
    queue = await broadcaster.subscribe(session_id)

    request = SubmitProposalRequest(session_id=session_id, text="Test")
    await service.submit_proposal(request)

    # Verify event was broadcast
    event = queue.get_nowait()
    assert event.event_type == EventType.PROPOSAL_CREATED
    assert event.proposal.text == "Test"

  @pytest.mark.asyncio
  async def test_persists_proposal(
    self,
    service: ProposalService,
    repository: InMemorySessionRepository,
  ) -> None:
    """SubmitProposal persists the proposal in the repository."""
    session = await service.create_session(CreateSessionRequest())
    session_id = session.session.session_id

    request = SubmitProposalRequest(session_id=session_id, text="Test")
    response = await service.submit_proposal(request)

    stored_session = await repository.get_session(session_id)
    assert stored_session is not None
    assert len(stored_session.proposals) == 1
    assert stored_session.proposals[0].proposal_id == response.proposal.proposal_id


class TestSubmitDecision(TestProposalService):
  """Tests for SubmitDecision RPC."""

  @pytest.mark.asyncio
  async def test_approve_sets_approved_status(self, service: ProposalService) -> None:
    """SubmitDecision with approved=True sets APPROVED status."""
    session = await service.create_session(CreateSessionRequest())
    proposal = await service.submit_proposal(
      SubmitProposalRequest(
        session_id=session.session.session_id,
        text="Test",
      )
    )

    request = SubmitDecisionRequest(
      session_id=session.session.session_id,
      proposal_id=proposal.proposal.proposal_id,
      approved=True,
    )
    response = await service.submit_decision(request)

    assert response.proposal.status == ProposalStatus.APPROVED

  @pytest.mark.asyncio
  async def test_reject_sets_rejected_status(self, service: ProposalService) -> None:
    """SubmitDecision with approved=False sets REJECTED status."""
    session = await service.create_session(CreateSessionRequest())
    proposal = await service.submit_proposal(
      SubmitProposalRequest(
        session_id=session.session.session_id,
        text="Test",
      )
    )

    request = SubmitDecisionRequest(
      session_id=session.session.session_id,
      proposal_id=proposal.proposal.proposal_id,
      approved=False,
    )
    response = await service.submit_decision(request)

    assert response.proposal.status == ProposalStatus.REJECTED

  @pytest.mark.asyncio
  async def test_raises_not_found_for_nonexistent_session(
    self, service: ProposalService
  ) -> None:
    """SubmitDecision raises NOT_FOUND for nonexistent session."""
    request = SubmitDecisionRequest(
      session_id="nonexistent",
      proposal_id="some-proposal",
      approved=True,
    )

    with pytest.raises(grpclib.GRPCError) as exc_info:
      await service.submit_decision(request)

    assert exc_info.value.status == grpclib.const.Status.NOT_FOUND

  @pytest.mark.asyncio
  async def test_raises_not_found_for_nonexistent_proposal(
    self, service: ProposalService
  ) -> None:
    """SubmitDecision raises NOT_FOUND for nonexistent proposal."""
    session = await service.create_session(CreateSessionRequest())

    request = SubmitDecisionRequest(
      session_id=session.session.session_id,
      proposal_id="nonexistent",
      approved=True,
    )

    with pytest.raises(grpclib.GRPCError) as exc_info:
      await service.submit_decision(request)

    assert exc_info.value.status == grpclib.const.Status.NOT_FOUND

  @pytest.mark.asyncio
  async def test_broadcasts_proposal_updated_event(
    self,
    service: ProposalService,
    broadcaster: EventBroadcaster,
  ) -> None:
    """SubmitDecision broadcasts a PROPOSAL_UPDATED event."""
    session = await service.create_session(CreateSessionRequest())
    session_id = session.session.session_id

    # Subscribe BEFORE creating proposal so we receive the creation event
    queue = await broadcaster.subscribe(session_id)

    proposal = await service.submit_proposal(
      SubmitProposalRequest(session_id=session_id, text="Test")
    )

    # Drain the PROPOSAL_CREATED event
    queue.get_nowait()

    request = SubmitDecisionRequest(
      session_id=session_id,
      proposal_id=proposal.proposal.proposal_id,
      approved=True,
    )
    await service.submit_decision(request)

    # Verify event was broadcast
    event = queue.get_nowait()
    assert event.event_type == EventType.PROPOSAL_UPDATED


class TestSubscribe(TestProposalService):
  """Tests for Subscribe RPC."""

  @pytest.mark.asyncio
  async def test_raises_not_found_for_nonexistent_session(
    self, service: ProposalService
  ) -> None:
    """Subscribe raises NOT_FOUND for nonexistent session."""
    request = SubscribeRequest(session_id="nonexistent", client_id="client-1")

    with pytest.raises(grpclib.GRPCError) as exc_info:
      async for _ in service.subscribe(request):
        pass

    assert exc_info.value.status == grpclib.const.Status.NOT_FOUND

  @pytest.mark.asyncio
  async def test_replays_existing_proposals(self, service: ProposalService) -> None:
    """Subscribe replays existing proposals as history."""
    session = await service.create_session(CreateSessionRequest())
    session_id = session.session.session_id

    # Add some proposals before subscribing
    await service.submit_proposal(
      SubmitProposalRequest(session_id=session_id, text="First")
    )
    await service.submit_proposal(
      SubmitProposalRequest(session_id=session_id, text="Second")
    )

    request = SubscribeRequest(session_id=session_id, client_id="client-1")
    events: list[SessionEvent] = []

    async def collect_events() -> None:
      async for response in service.subscribe(request):
        events.append(response.event)
        if len(events) >= 2:
          break

    # Run with timeout to avoid hanging
    await asyncio.wait_for(collect_events(), timeout=1.0)

    assert len(events) == 2
    # Check that proposals are replayed with proposal_created field set
    assert events[0].proposal_created.text == "First"
    assert events[1].proposal_created.text == "Second"

  @pytest.mark.asyncio
  async def test_receives_live_events(
    self,
    service: ProposalService,
    broadcaster: EventBroadcaster,
  ) -> None:
    """Subscribe receives live events after subscribing via broadcaster."""
    session = await service.create_session(CreateSessionRequest())
    session_id = session.session.session_id

    # Subscribe directly to the broadcaster to verify live event delivery
    queue = await broadcaster.subscribe(session_id)

    # Submit a proposal - should be broadcast
    await service.submit_proposal(
      SubmitProposalRequest(session_id=session_id, text="Live proposal")
    )

    # Verify the event was received
    event = queue.get_nowait()
    assert event.event_type == EventType.PROPOSAL_CREATED
    assert event.proposal.text == "Live proposal"
