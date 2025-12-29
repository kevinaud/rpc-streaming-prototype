"""Unit tests for proposal loop using FakeProposalServiceStub."""

import sys
from pathlib import Path

# Add project root to path for fixture imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from rpc_stream_prototype.generated.proposal.v1 import (
  CreateSessionRequest,
  GetSessionRequest,
  ProposalStatus,
  SubmitProposalRequest,
  SubscribeRequest,
)
from tests.fixtures.fake_proposal_client import FakeProposalServiceStub


class TestFakeProposalServiceStub:
  """Tests for the FakeProposalServiceStub fixture."""

  async def test_create_session_returns_configured_id(self) -> None:
    """create_session should return the configured session ID."""
    fake = FakeProposalServiceStub()
    fake.session_id = "my-custom-session"

    response = await fake.create_session(CreateSessionRequest())

    assert response.session.session_id == "my-custom-session"
    assert fake.create_session_calls == 1

  async def test_get_session_returns_session_when_exists(self) -> None:
    """get_session should return session when exists."""
    fake = FakeProposalServiceStub()
    fake.session_exists = True

    response = await fake.get_session(GetSessionRequest(session_id="any-id"))
    assert response.session.session_id == "any-id"

  async def test_get_session_raises_when_not_exists(self) -> None:
    """get_session should raise when session doesn't exist."""
    import pytest

    fake = FakeProposalServiceStub()
    fake.session_exists = False

    with pytest.raises(Exception, match="not found"):
      await fake.get_session(GetSessionRequest(session_id="any-id"))

  async def test_get_session_tracks_calls(self) -> None:
    """get_session should track session IDs checked."""
    fake = FakeProposalServiceStub()

    await fake.get_session(GetSessionRequest(session_id="session-1"))
    await fake.get_session(GetSessionRequest(session_id="session-2"))

    assert fake.get_session_calls == ["session-1", "session-2"]

  async def test_submit_proposal_returns_pending_proposal(self) -> None:
    """submit_proposal should return a PENDING proposal."""
    fake = FakeProposalServiceStub()

    response = await fake.submit_proposal(
      SubmitProposalRequest(session_id="session-1", text="My proposal text")
    )

    assert response.proposal.text == "My proposal text"
    assert response.proposal.status == ProposalStatus.PENDING
    assert response.proposal.proposal_id == "proposal-1"

  async def test_submit_proposal_tracks_calls(self) -> None:
    """submit_proposal should track submitted proposals."""
    fake = FakeProposalServiceStub()

    await fake.submit_proposal(
      SubmitProposalRequest(session_id="session-1", text="First")
    )
    await fake.submit_proposal(
      SubmitProposalRequest(session_id="session-2", text="Second")
    )

    assert fake.submit_proposal_calls == [
      ("session-1", "First"),
      ("session-2", "Second"),
    ]

  async def test_subscribe_yields_configured_events(self) -> None:
    """subscribe should yield events configured via configure_decision."""
    fake = FakeProposalServiceStub()
    fake.configure_decision("proposal-1", approved=True)
    fake.configure_decision("proposal-2", approved=False)

    responses = [
      r
      async for r in fake.subscribe(
        SubscribeRequest(session_id="session-1", client_id="client-1")
      )
    ]

    assert len(responses) == 2
    assert responses[0].event.proposal_updated.proposal_id == "proposal-1"
    assert responses[0].event.proposal_updated.status == ProposalStatus.APPROVED
    assert responses[1].event.proposal_updated.proposal_id == "proposal-2"
    assert responses[1].event.proposal_updated.status == ProposalStatus.REJECTED

  async def test_subscribe_tracks_calls(self) -> None:
    """subscribe should track subscription requests."""
    fake = FakeProposalServiceStub()

    _ = [
      r
      async for r in fake.subscribe(
        SubscribeRequest(session_id="session-1", client_id="client-a")
      )
    ]
    _ = [
      r
      async for r in fake.subscribe(
        SubscribeRequest(session_id="session-2", client_id="client-b")
      )
    ]

    assert fake.subscribe_calls == [
      ("session-1", "client-a"),
      ("session-2", "client-b"),
    ]


class TestProposalLoopWithFake:
  """Tests for proposal loop behavior using FakeProposalServiceStub.

  These tests verify the logic flows correctly using the fake.
  Full integration testing requires a real server.
  """

  async def test_proposal_loop_imports_correctly(self) -> None:
    """proposal_loop module should import without errors."""
    from rpc_stream_prototype.cli.session.proposal_loop import (
      run_proposal_loop,
    )

    assert callable(run_proposal_loop)
