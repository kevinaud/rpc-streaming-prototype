"""Unit tests for proposal loop using FakeProposalClient."""

import sys
from pathlib import Path

# Add project root to path for fixture imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from rpc_stream_prototype.generated.proposal.v1 import (
  ProposalStatus,
)
from tests.fixtures.fake_proposal_client import FakeProposalClient


class TestFakeProposalClient:
  """Tests for the FakeProposalClient fixture."""

  async def test_create_session_returns_configured_id(self) -> None:
    """create_session should return the configured session ID."""
    fake = FakeProposalClient()
    fake.session_id = "my-custom-session"

    result = await fake.create_session()

    assert result == "my-custom-session"
    assert fake.create_session_calls == 1

  async def test_get_session_returns_configured_exists_state(self) -> None:
    """get_session should return the configured exists state."""
    fake = FakeProposalClient()
    fake.session_exists = True

    assert await fake.get_session("any-id") is True
    fake.session_exists = False
    assert await fake.get_session("any-id") is False

  async def test_get_session_tracks_calls(self) -> None:
    """get_session should track session IDs checked."""
    fake = FakeProposalClient()

    await fake.get_session("session-1")
    await fake.get_session("session-2")

    assert fake.get_session_calls == ["session-1", "session-2"]

  async def test_submit_proposal_returns_pending_proposal(self) -> None:
    """submit_proposal should return a PENDING proposal."""
    fake = FakeProposalClient()

    proposal = await fake.submit_proposal("session-1", "My proposal text")

    assert proposal.text == "My proposal text"
    assert proposal.status == ProposalStatus.PENDING
    assert proposal.proposal_id == "proposal-1"

  async def test_submit_proposal_tracks_calls(self) -> None:
    """submit_proposal should track submitted proposals."""
    fake = FakeProposalClient()

    await fake.submit_proposal("session-1", "First")
    await fake.submit_proposal("session-2", "Second")

    assert fake.submit_proposal_calls == [
      ("session-1", "First"),
      ("session-2", "Second"),
    ]

  async def test_subscribe_yields_configured_events(self) -> None:
    """subscribe should yield events configured via configure_decision."""
    fake = FakeProposalClient()
    fake.configure_decision("proposal-1", approved=True)
    fake.configure_decision("proposal-2", approved=False)

    events = [e async for e in fake.subscribe("session-1", "client-1")]

    assert len(events) == 2
    assert events[0].proposal_updated.proposal_id == "proposal-1"
    assert events[0].proposal_updated.status == ProposalStatus.APPROVED
    assert events[1].proposal_updated.proposal_id == "proposal-2"
    assert events[1].proposal_updated.status == ProposalStatus.REJECTED

  async def test_subscribe_tracks_calls(self) -> None:
    """subscribe should track subscription requests."""
    fake = FakeProposalClient()

    _ = [e async for e in fake.subscribe("session-1", "client-a")]
    _ = [e async for e in fake.subscribe("session-2", "client-b")]

    assert fake.subscribe_calls == [
      ("session-1", "client-a"),
      ("session-2", "client-b"),
    ]

  async def test_session_context_manager(self) -> None:
    """session() should provide async context manager."""
    fake = FakeProposalClient()

    assert not fake.connected

    async for client in fake.session():
      assert client.connected
      assert client is fake

    assert fake.closed
    assert not fake.connected


class TestProposalLoopWithFake:
  """Tests for proposal loop behavior using FakeProposalClient.

  These tests verify the logic flows correctly using the fake.
  Full integration testing requires a real server.
  """

  async def test_proposal_loop_imports_correctly(self) -> None:
    """proposal_loop module should import without errors."""
    from rpc_stream_prototype.cli.session.proposal_loop import (
      run_proposal_loop,
    )

    assert callable(run_proposal_loop)
