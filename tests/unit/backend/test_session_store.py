"""Unit tests for the SessionStore."""

from typing import TYPE_CHECKING

import pytest

from rpc_stream_prototype.backend.storage.exceptions import (
  ProposalNotFoundError,
  SessionNotFoundError,
)
from rpc_stream_prototype.backend.storage.session_store import SessionStore
from rpc_stream_prototype.generated.proposal.v1 import ProposalStatus

if TYPE_CHECKING:
  from collections.abc import AsyncGenerator

  from rpc_stream_prototype.generated.proposal.v1 import SessionEvent


class TestSessionStore:
  """Tests for SessionStore."""

  @pytest.fixture
  async def store(self) -> AsyncGenerator[SessionStore]:
    """Create a connected store for each test."""
    _store = SessionStore()
    await _store.connect()
    yield _store
    await _store.disconnect()


class TestCreateSession(TestSessionStore):
  """Tests for create_session."""

  @pytest.mark.asyncio
  async def test_returns_session_with_id(self, store: SessionStore) -> None:
    """create_session returns a session with a valid UUID."""
    session = await store.create_session()

    assert session.session_id is not None
    assert len(session.session_id) == 36  # UUID format

  @pytest.mark.asyncio
  async def test_creates_unique_sessions(self, store: SessionStore) -> None:
    """create_session creates unique session IDs."""
    session1 = await store.create_session()
    session2 = await store.create_session()

    assert session1.session_id != session2.session_id


class TestGetSession(TestSessionStore):
  """Tests for get_session."""

  @pytest.mark.asyncio
  async def test_returns_existing_session(self, store: SessionStore) -> None:
    """get_session returns an existing session."""
    created = await store.create_session()

    retrieved = await store.get_session(created.session_id)

    assert retrieved is not None
    assert retrieved.session_id == created.session_id

  @pytest.mark.asyncio
  async def test_returns_none_for_nonexistent(self, store: SessionStore) -> None:
    """get_session returns None for nonexistent session."""
    result = await store.get_session("nonexistent-id")

    assert result is None


class TestSessionExists(TestSessionStore):
  """Tests for session_exists."""

  @pytest.mark.asyncio
  async def test_returns_true_for_existing(self, store: SessionStore) -> None:
    """session_exists returns True for existing session."""
    session = await store.create_session()

    exists = await store.session_exists(session.session_id)

    assert exists is True

  @pytest.mark.asyncio
  async def test_returns_false_for_nonexistent(self, store: SessionStore) -> None:
    """session_exists returns False for nonexistent session."""
    exists = await store.session_exists("nonexistent-id")

    assert exists is False


class TestAddProposal(TestSessionStore):
  """Tests for add_proposal."""

  @pytest.mark.asyncio
  async def test_returns_created_proposal(self, store: SessionStore) -> None:
    """add_proposal returns the created proposal."""
    session = await store.create_session()

    proposal = await store.add_proposal(session.session_id, "Test proposal")

    assert proposal is not None
    assert proposal.text == "Test proposal"
    assert proposal.status == ProposalStatus.PENDING
    assert len(proposal.proposal_id) == 36  # UUID format

  @pytest.mark.asyncio
  async def test_raises_for_nonexistent_session(self, store: SessionStore) -> None:
    """add_proposal raises SessionNotFoundError for nonexistent session."""
    with pytest.raises(SessionNotFoundError) as exc_info:
      await store.add_proposal("nonexistent", "Test")

    assert exc_info.value.session_id == "nonexistent"

  @pytest.mark.asyncio
  async def test_proposal_added_to_session(self, store: SessionStore) -> None:
    """add_proposal adds the proposal to the session's list."""
    session = await store.create_session()
    await store.add_proposal(session.session_id, "Proposal 1")
    await store.add_proposal(session.session_id, "Proposal 2")

    proposals = await store.get_proposals(session.session_id)

    assert len(proposals) == 2
    assert proposals[0].text == "Proposal 1"
    assert proposals[1].text == "Proposal 2"


class TestUpdateProposal(TestSessionStore):
  """Tests for update_proposal."""

  @pytest.mark.asyncio
  async def test_approve_proposal(self, store: SessionStore) -> None:
    """update_proposal can approve a proposal."""
    session = await store.create_session()
    proposal = await store.add_proposal(session.session_id, "Test")

    updated = await store.update_proposal(
      session.session_id,
      proposal.proposal_id,
      approved=True,
    )

    assert updated.status == ProposalStatus.APPROVED

  @pytest.mark.asyncio
  async def test_reject_proposal(self, store: SessionStore) -> None:
    """update_proposal can reject a proposal."""
    session = await store.create_session()
    proposal = await store.add_proposal(session.session_id, "Test")

    updated = await store.update_proposal(
      session.session_id,
      proposal.proposal_id,
      approved=False,
    )

    assert updated.status == ProposalStatus.REJECTED

  @pytest.mark.asyncio
  async def test_raises_for_nonexistent_session(self, store: SessionStore) -> None:
    """update_proposal raises SessionNotFoundError for nonexistent session."""
    with pytest.raises(SessionNotFoundError) as exc_info:
      await store.update_proposal(
        "nonexistent-session",
        "some-proposal",
        approved=True,
      )

    assert exc_info.value.session_id == "nonexistent-session"

  @pytest.mark.asyncio
  async def test_raises_for_nonexistent_proposal(self, store: SessionStore) -> None:
    """update_proposal raises ProposalNotFoundError for nonexistent proposal."""
    session = await store.create_session()

    with pytest.raises(ProposalNotFoundError) as exc_info:
      await store.update_proposal(
        session.session_id,
        "nonexistent-proposal",
        approved=True,
      )

    assert exc_info.value.session_id == session.session_id
    assert exc_info.value.proposal_id == "nonexistent-proposal"


class TestGetProposals(TestSessionStore):
  """Tests for get_proposals."""

  @pytest.mark.asyncio
  async def test_returns_empty_for_new_session(self, store: SessionStore) -> None:
    """get_proposals returns empty list for new session."""
    session = await store.create_session()

    proposals = await store.get_proposals(session.session_id)

    assert proposals == []

  @pytest.mark.asyncio
  async def test_returns_empty_for_nonexistent_session(
    self, store: SessionStore
  ) -> None:
    """get_proposals returns empty list for nonexistent session."""
    proposals = await store.get_proposals("nonexistent")

    assert proposals == []

  @pytest.mark.asyncio
  async def test_returns_all_proposals(self, store: SessionStore) -> None:
    """get_proposals returns all proposals in order."""
    session = await store.create_session()
    await store.add_proposal(session.session_id, "First")
    await store.add_proposal(session.session_id, "Second")
    await store.add_proposal(session.session_id, "Third")

    proposals = await store.get_proposals(session.session_id)

    assert len(proposals) == 3
    assert [p.text for p in proposals] == ["First", "Second", "Third"]


class TestWatchSession(TestSessionStore):
  """Tests for watch_session."""

  @pytest.mark.asyncio
  async def test_yields_history_first(self, store: SessionStore) -> None:
    """watch_session yields existing proposals as history."""
    session = await store.create_session()
    await store.add_proposal(session.session_id, "Historical 1")
    await store.add_proposal(session.session_id, "Historical 2")

    events: list[SessionEvent] = []
    async for event in store.watch_session(session.session_id):
      events.append(event)
      if len(events) >= 2:
        break

    assert len(events) == 2
    assert events[0].proposal_created.text == "Historical 1"
    assert events[1].proposal_created.text == "Historical 2"

  @pytest.mark.asyncio
  async def test_yields_live_events(self, store: SessionStore) -> None:
    """watch_session yields live events after history."""
    import asyncio

    session = await store.create_session()
    events: list[SessionEvent] = []
    received_event = asyncio.Event()

    async def watch() -> None:
      async for event in store.watch_session(session.session_id):
        events.append(event)
        received_event.set()
        break

    # Start watching in background
    watch_task = asyncio.create_task(watch())

    # Give the watcher time to subscribe
    await asyncio.sleep(0.05)

    # Add a proposal (this should trigger a live event)
    await store.add_proposal(session.session_id, "Live proposal")

    # Wait for event to be received
    await asyncio.wait_for(received_event.wait(), timeout=1.0)
    watch_task.cancel()

    assert len(events) == 1
    assert events[0].proposal_created.text == "Live proposal"

  @pytest.mark.asyncio
  async def test_history_shows_updated_status(self, store: SessionStore) -> None:
    """watch_session shows updated proposals as proposal_updated."""
    session = await store.create_session()
    proposal = await store.add_proposal(session.session_id, "To be approved")
    await store.update_proposal(session.session_id, proposal.proposal_id, approved=True)

    events: list[SessionEvent] = []
    async for event in store.watch_session(session.session_id):
      events.append(event)
      if len(events) >= 1:
        break

    assert len(events) == 1
    # Approved proposals should come as proposal_updated
    assert events[0].proposal_updated is not None
    assert events[0].proposal_updated.status == ProposalStatus.APPROVED
