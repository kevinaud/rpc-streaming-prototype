"""End-to-end integration tests for the gRPC server."""

import asyncio
from typing import TYPE_CHECKING

import pytest
from grpclib.testing import ChannelFor

from rpc_stream_prototype.backend.services.proposal_service import ProposalService
from rpc_stream_prototype.backend.storage.session_store import SessionStore
from rpc_stream_prototype.generated.proposal.v1 import (
  CreateSessionRequest,
  GetSessionRequest,
  ProposalServiceStub,
  ProposalStatus,
  SubmitDecisionRequest,
  SubmitProposalRequest,
  SubscribeRequest,
)

if TYPE_CHECKING:
  from collections.abc import AsyncGenerator

  from grpclib.client import Channel

  from rpc_stream_prototype.generated.proposal.v1 import (
    Proposal,
    SessionEvent,
  )


@pytest.fixture
async def store() -> AsyncGenerator[SessionStore]:
  """Create a connected store for each test."""
  _store = SessionStore()
  await _store.connect()
  yield _store
  await _store.disconnect()


@pytest.fixture
def service(store: SessionStore) -> ProposalService:
  """Create a fresh service with real dependencies."""
  return ProposalService(store)


@pytest.fixture
async def channel(service: ProposalService) -> AsyncGenerator[Channel]:
  """Create a test channel connected to the service."""
  async with ChannelFor([service]) as channel:
    yield channel


@pytest.fixture
def stub(channel: Channel) -> ProposalServiceStub:
  """Create a client stub connected to the test channel."""
  return ProposalServiceStub(channel)


class TestServerE2E:
  """End-to-end tests using gRPC client and server."""

  @pytest.mark.asyncio
  async def test_create_session_via_grpc(self, stub: ProposalServiceStub) -> None:
    """CreateSession works via gRPC client."""
    response = await stub.create_session(CreateSessionRequest())

    assert response.session is not None
    assert len(response.session.session_id) == 36

  @pytest.mark.asyncio
  async def test_get_session_via_grpc(self, stub: ProposalServiceStub) -> None:
    """GetSession returns created session via gRPC."""
    create_response = await stub.create_session(CreateSessionRequest())
    session_id = create_response.session.session_id

    get_response = await stub.get_session(GetSessionRequest(session_id=session_id))

    assert get_response.session.session_id == session_id

  @pytest.mark.asyncio
  async def test_submit_proposal_via_grpc(self, stub: ProposalServiceStub) -> None:
    """SubmitProposal creates proposal via gRPC."""
    session = await stub.create_session(CreateSessionRequest())

    response = await stub.submit_proposal(
      SubmitProposalRequest(
        session_id=session.session.session_id,
        text="Test proposal via gRPC",
      )
    )

    assert response.proposal.text == "Test proposal via gRPC"
    assert response.proposal.status == ProposalStatus.PENDING

  @pytest.mark.asyncio
  async def test_submit_decision_approve_via_grpc(
    self, stub: ProposalServiceStub
  ) -> None:
    """SubmitDecision approves proposal via gRPC."""
    session = await stub.create_session(CreateSessionRequest())
    proposal = await stub.submit_proposal(
      SubmitProposalRequest(
        session_id=session.session.session_id,
        text="Test",
      )
    )

    response = await stub.submit_decision(
      SubmitDecisionRequest(
        session_id=session.session.session_id,
        proposal_id=proposal.proposal.proposal_id,
        approved=True,
      )
    )

    assert response.proposal.status == ProposalStatus.APPROVED

  @pytest.mark.asyncio
  async def test_submit_decision_reject_via_grpc(
    self, stub: ProposalServiceStub
  ) -> None:
    """SubmitDecision rejects proposal via gRPC."""
    session = await stub.create_session(CreateSessionRequest())
    proposal = await stub.submit_proposal(
      SubmitProposalRequest(
        session_id=session.session.session_id,
        text="Test",
      )
    )

    response = await stub.submit_decision(
      SubmitDecisionRequest(
        session_id=session.session.session_id,
        proposal_id=proposal.proposal.proposal_id,
        approved=False,
      )
    )

    assert response.proposal.status == ProposalStatus.REJECTED

  @pytest.mark.asyncio
  async def test_subscribe_receives_history_via_grpc(
    self, stub: ProposalServiceStub
  ) -> None:
    """Subscribe replays history via gRPC streaming."""
    session = await stub.create_session(CreateSessionRequest())
    session_id = session.session.session_id

    # Create some proposals first
    await stub.submit_proposal(
      SubmitProposalRequest(session_id=session_id, text="First")
    )
    await stub.submit_proposal(
      SubmitProposalRequest(session_id=session_id, text="Second")
    )

    # Subscribe and collect history
    events: list[SessionEvent] = []
    async for response in stub.subscribe(
      SubscribeRequest(session_id=session_id, client_id="test-client")
    ):
      events.append(response.event)
      if len(events) >= 2:
        break

    assert len(events) == 2
    assert events[0].proposal_created.text == "First"
    assert events[1].proposal_created.text == "Second"

  @pytest.mark.asyncio
  async def test_full_workflow_via_grpc(self, stub: ProposalServiceStub) -> None:
    """Complete approval workflow via gRPC."""
    # 1. Create session
    session = await stub.create_session(CreateSessionRequest())
    session_id = session.session.session_id

    # 2. Submit proposal
    proposal_response = await stub.submit_proposal(
      SubmitProposalRequest(session_id=session_id, text="Please approve this")
    )
    assert proposal_response.proposal.status == ProposalStatus.PENDING

    # 3. Approve proposal
    decision_response = await stub.submit_decision(
      SubmitDecisionRequest(
        session_id=session_id,
        proposal_id=proposal_response.proposal.proposal_id,
        approved=True,
      )
    )
    assert decision_response.proposal.status == ProposalStatus.APPROVED

    # 4. Verify via subscribe (history replay)
    events: list[SessionEvent] = []
    async for response in stub.subscribe(
      SubscribeRequest(session_id=session_id, client_id="verifier")
    ):
      events.append(response.event)
      if len(events) >= 1:
        break

    # Should show the approved proposal
    assert events[0].proposal_updated.status == ProposalStatus.APPROVED

  @pytest.mark.asyncio
  async def test_subscribe_live_events_via_grpc(
    self, stub: ProposalServiceStub
  ) -> None:
    """Subscribe receives live events after history replay."""
    session = await stub.create_session(CreateSessionRequest())
    session_id = session.session.session_id

    events: list[SessionEvent] = []
    received_event = asyncio.Event()

    async def subscribe_and_collect() -> None:
      async for response in stub.subscribe(
        SubscribeRequest(session_id=session_id, client_id="test-client")
      ):
        events.append(response.event)
        received_event.set()
        break

    # Start subscribing in background
    subscribe_task = asyncio.create_task(subscribe_and_collect())

    # Wait a bit for subscription to be established
    await asyncio.sleep(0.05)

    # Submit a proposal (should trigger live event)
    await stub.submit_proposal(
      SubmitProposalRequest(session_id=session_id, text="Live proposal")
    )

    # Wait for event
    await asyncio.wait_for(received_event.wait(), timeout=2.0)
    subscribe_task.cancel()

    assert len(events) == 1
    assert events[0].proposal_created.text == "Live proposal"

  @pytest.mark.asyncio
  async def test_multiple_proposals_and_decisions(
    self, stub: ProposalServiceStub
  ) -> None:
    """Multiple proposals can be submitted and decided."""
    session = await stub.create_session(CreateSessionRequest())
    session_id = session.session.session_id

    # Submit multiple proposals
    proposals: list[Proposal] = []
    for i in range(3):
      response = await stub.submit_proposal(
        SubmitProposalRequest(session_id=session_id, text=f"Proposal {i}")
      )
      proposals.append(response.proposal)

    # Approve first, reject second, leave third pending
    await stub.submit_decision(
      SubmitDecisionRequest(
        session_id=session_id,
        proposal_id=proposals[0].proposal_id,
        approved=True,
      )
    )
    await stub.submit_decision(
      SubmitDecisionRequest(
        session_id=session_id,
        proposal_id=proposals[1].proposal_id,
        approved=False,
      )
    )

    # Subscribe and verify history
    events: list[SessionEvent] = []
    async for response in stub.subscribe(
      SubscribeRequest(session_id=session_id, client_id="verifier")
    ):
      events.append(response.event)
      if len(events) >= 3:
        break

    # First two should be updates (approved/rejected), third should be created
    assert events[0].proposal_updated.status == ProposalStatus.APPROVED
    assert events[1].proposal_updated.status == ProposalStatus.REJECTED
    assert events[2].proposal_created.status == ProposalStatus.PENDING
