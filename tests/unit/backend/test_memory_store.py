"""Unit tests for the in-memory session repository."""

import pytest

from rpc_stream_prototype.backend.models.domain import Proposal, ProposalStatus
from rpc_stream_prototype.backend.storage.memory_store import InMemorySessionRepository


class TestInMemorySessionRepository:
  """Tests for InMemorySessionRepository."""

  @pytest.fixture
  def repository(self) -> InMemorySessionRepository:
    """Create a fresh repository for each test."""
    return InMemorySessionRepository()

  @pytest.mark.asyncio
  async def test_create_session_returns_session(
    self, repository: InMemorySessionRepository
  ) -> None:
    """create_session() returns a new session with UUID."""
    session = await repository.create_session()

    assert session is not None
    assert len(session.session_id) == 36  # UUID format

  @pytest.mark.asyncio
  async def test_create_session_generates_unique_ids(
    self, repository: InMemorySessionRepository
  ) -> None:
    """create_session() generates unique session IDs."""
    session1 = await repository.create_session()
    session2 = await repository.create_session()

    assert session1.session_id != session2.session_id

  @pytest.mark.asyncio
  async def test_get_session_found(self, repository: InMemorySessionRepository) -> None:
    """get_session() returns session when found."""
    created = await repository.create_session()

    retrieved = await repository.get_session(created.session_id)

    assert retrieved is not None
    assert retrieved.session_id == created.session_id

  @pytest.mark.asyncio
  async def test_get_session_not_found(
    self, repository: InMemorySessionRepository
  ) -> None:
    """get_session() returns None when not found."""
    result = await repository.get_session("nonexistent-id")

    assert result is None

  @pytest.mark.asyncio
  async def test_add_proposal_success(
    self, repository: InMemorySessionRepository
  ) -> None:
    """add_proposal() adds proposal to existing session."""
    session = await repository.create_session()
    proposal = Proposal.create(session_id=session.session_id, text="test")

    result = await repository.add_proposal(session.session_id, proposal)

    assert result is not None
    assert result.proposal_id == proposal.proposal_id

  @pytest.mark.asyncio
  async def test_add_proposal_session_not_found(
    self, repository: InMemorySessionRepository
  ) -> None:
    """add_proposal() returns None when session doesn't exist."""
    proposal = Proposal.create(session_id="nonexistent", text="test")

    result = await repository.add_proposal("nonexistent", proposal)

    assert result is None

  @pytest.mark.asyncio
  async def test_add_proposal_persists(
    self, repository: InMemorySessionRepository
  ) -> None:
    """add_proposal() persists the proposal in the session."""
    session = await repository.create_session()
    proposal = Proposal.create(session_id=session.session_id, text="test")

    await repository.add_proposal(session.session_id, proposal)

    retrieved = await repository.get_session(session.session_id)
    assert retrieved is not None
    assert len(retrieved.proposals) == 1
    assert retrieved.proposals[0].proposal_id == proposal.proposal_id

  @pytest.mark.asyncio
  async def test_update_proposal_approve(
    self, repository: InMemorySessionRepository
  ) -> None:
    """update_proposal() with approved=True sets APPROVED status."""
    session = await repository.create_session()
    proposal = Proposal.create(session_id=session.session_id, text="test")
    await repository.add_proposal(session.session_id, proposal)

    result = await repository.update_proposal(
      session.session_id, proposal.proposal_id, approved=True
    )

    assert result is not None
    assert result.status == ProposalStatus.APPROVED

  @pytest.mark.asyncio
  async def test_update_proposal_reject(
    self, repository: InMemorySessionRepository
  ) -> None:
    """update_proposal() with approved=False sets REJECTED status."""
    session = await repository.create_session()
    proposal = Proposal.create(session_id=session.session_id, text="test")
    await repository.add_proposal(session.session_id, proposal)

    result = await repository.update_proposal(
      session.session_id, proposal.proposal_id, approved=False
    )

    assert result is not None
    assert result.status == ProposalStatus.REJECTED

  @pytest.mark.asyncio
  async def test_update_proposal_session_not_found(
    self, repository: InMemorySessionRepository
  ) -> None:
    """update_proposal() returns None when session doesn't exist."""
    result = await repository.update_proposal(
      "nonexistent", "proposal-id", approved=True
    )

    assert result is None

  @pytest.mark.asyncio
  async def test_update_proposal_proposal_not_found(
    self, repository: InMemorySessionRepository
  ) -> None:
    """update_proposal() returns None when proposal doesn't exist."""
    session = await repository.create_session()

    result = await repository.update_proposal(
      session.session_id, "nonexistent", approved=True
    )

    assert result is None

  @pytest.mark.asyncio
  async def test_update_proposal_persists(
    self, repository: InMemorySessionRepository
  ) -> None:
    """update_proposal() persists the status change."""
    session = await repository.create_session()
    proposal = Proposal.create(session_id=session.session_id, text="test")
    await repository.add_proposal(session.session_id, proposal)

    await repository.update_proposal(
      session.session_id, proposal.proposal_id, approved=True
    )

    retrieved = await repository.get_session(session.session_id)
    assert retrieved is not None
    assert retrieved.proposals[0].status == ProposalStatus.APPROVED

  @pytest.mark.asyncio
  async def test_multiple_proposals_in_session(
    self, repository: InMemorySessionRepository
  ) -> None:
    """Multiple proposals can be added to a single session."""
    session = await repository.create_session()

    for i in range(5):
      proposal = Proposal.create(session_id=session.session_id, text=f"proposal {i}")
      await repository.add_proposal(session.session_id, proposal)

    retrieved = await repository.get_session(session.session_id)
    assert retrieved is not None
    assert len(retrieved.proposals) == 5

  @pytest.mark.asyncio
  async def test_multiple_sessions_isolated(
    self, repository: InMemorySessionRepository
  ) -> None:
    """Proposals in different sessions are isolated."""
    session1 = await repository.create_session()
    session2 = await repository.create_session()

    proposal1 = Proposal.create(session_id=session1.session_id, text="session 1")
    proposal2 = Proposal.create(session_id=session2.session_id, text="session 2")

    await repository.add_proposal(session1.session_id, proposal1)
    await repository.add_proposal(session2.session_id, proposal2)

    retrieved1 = await repository.get_session(session1.session_id)
    retrieved2 = await repository.get_session(session2.session_id)

    assert retrieved1 is not None
    assert retrieved2 is not None
    assert len(retrieved1.proposals) == 1
    assert len(retrieved2.proposals) == 1
    assert retrieved1.proposals[0].text == "session 1"
    assert retrieved2.proposals[0].text == "session 2"
