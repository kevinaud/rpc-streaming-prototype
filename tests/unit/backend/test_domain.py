"""Unit tests for domain models."""

from datetime import UTC, datetime

from rpc_stream_prototype.backend.models.domain import (
  Proposal,
  ProposalStatus,
  Session,
)


class TestProposalStatus:
  """Tests for ProposalStatus enum."""

  def test_status_values(self) -> None:
    """All expected status values exist."""
    assert ProposalStatus.PENDING.value == "pending"
    assert ProposalStatus.APPROVED.value == "approved"
    assert ProposalStatus.REJECTED.value == "rejected"


class TestProposal:
  """Tests for Proposal dataclass."""

  def test_create_generates_uuid(self) -> None:
    """create() generates a unique proposal_id."""
    proposal = Proposal.create(session_id="test-session", text="test text")
    assert proposal.proposal_id is not None
    assert len(proposal.proposal_id) == 36  # UUID format

  def test_create_sets_pending_status(self) -> None:
    """create() sets status to PENDING."""
    proposal = Proposal.create(session_id="test-session", text="test text")
    assert proposal.status == ProposalStatus.PENDING

  def test_create_sets_session_id(self) -> None:
    """create() sets the session_id correctly."""
    proposal = Proposal.create(session_id="my-session", text="text")
    assert proposal.session_id == "my-session"

  def test_create_sets_text(self) -> None:
    """create() sets the text correctly."""
    proposal = Proposal.create(session_id="session", text="my proposal text")
    assert proposal.text == "my proposal text"

  def test_create_sets_timestamp(self) -> None:
    """create() sets created_at to current time."""
    before = datetime.now(UTC)
    proposal = Proposal.create(session_id="session", text="text")
    after = datetime.now(UTC)

    assert before <= proposal.created_at <= after

  def test_approve_returns_approved_proposal(self) -> None:
    """approve() returns a new Proposal with APPROVED status."""
    original = Proposal.create(session_id="session", text="text")
    approved = original.approve()

    assert approved.status == ProposalStatus.APPROVED
    assert approved.proposal_id == original.proposal_id
    assert approved.text == original.text
    assert approved.session_id == original.session_id
    assert approved.created_at == original.created_at

  def test_approve_does_not_mutate_original(self) -> None:
    """approve() does not mutate the original proposal."""
    original = Proposal.create(session_id="session", text="text")
    original.approve()

    assert original.status == ProposalStatus.PENDING

  def test_reject_returns_rejected_proposal(self) -> None:
    """reject() returns a new Proposal with REJECTED status."""
    original = Proposal.create(session_id="session", text="text")
    rejected = original.reject()

    assert rejected.status == ProposalStatus.REJECTED
    assert rejected.proposal_id == original.proposal_id
    assert rejected.text == original.text

  def test_reject_does_not_mutate_original(self) -> None:
    """reject() does not mutate the original proposal."""
    original = Proposal.create(session_id="session", text="text")
    original.reject()

    assert original.status == ProposalStatus.PENDING


class TestSession:
  """Tests for Session dataclass."""

  def test_create_generates_uuid(self) -> None:
    """create() generates a unique session_id."""
    session = Session.create()
    assert session.session_id is not None
    assert len(session.session_id) == 36  # UUID format

  def test_create_initializes_empty_proposals(self) -> None:
    """create() initializes with empty proposals list."""
    session = Session.create()
    assert session.proposals == []

  def test_create_sets_timestamp(self) -> None:
    """create() sets created_at to current time."""
    before = datetime.now(UTC)
    session = Session.create()
    after = datetime.now(UTC)

    assert before <= session.created_at <= after

  def test_add_proposal(self) -> None:
    """add_proposal() adds proposal to the list."""
    session = Session.create()
    proposal = Proposal.create(session_id=session.session_id, text="test")

    session.add_proposal(proposal)

    assert len(session.proposals) == 1
    assert session.proposals[0] == proposal

  def test_get_proposal_found(self) -> None:
    """get_proposal() returns proposal when found."""
    session = Session.create()
    proposal = Proposal.create(session_id=session.session_id, text="test")
    session.add_proposal(proposal)

    result = session.get_proposal(proposal.proposal_id)

    assert result == proposal

  def test_get_proposal_not_found(self) -> None:
    """get_proposal() returns None when not found."""
    session = Session.create()

    result = session.get_proposal("nonexistent-id")

    assert result is None

  def test_get_pending_proposals_returns_only_pending(self) -> None:
    """get_pending_proposals() filters by PENDING status."""
    session = Session.create()
    p1 = Proposal.create(session_id=session.session_id, text="pending")
    p2 = Proposal.create(session_id=session.session_id, text="approved")
    p3 = Proposal.create(session_id=session.session_id, text="also pending")

    session.add_proposal(p1)
    session.add_proposal(p2.approve())
    session.add_proposal(p3)

    pending = session.get_pending_proposals()

    assert len(pending) == 2
    assert p1 in pending
    assert p3 in pending

  def test_get_pending_proposals_empty_when_none_pending(self) -> None:
    """get_pending_proposals() returns empty list when no pending."""
    session = Session.create()
    proposal = Proposal.create(session_id=session.session_id, text="approved")
    session.add_proposal(proposal.approve())

    pending = session.get_pending_proposals()

    assert pending == []

  def test_update_proposal_success(self) -> None:
    """update_proposal() updates existing proposal."""
    session = Session.create()
    proposal = Proposal.create(session_id=session.session_id, text="test")
    session.add_proposal(proposal)

    updated = proposal.approve()
    result = session.update_proposal(updated)

    assert result is True
    assert session.proposals[0].status == ProposalStatus.APPROVED

  def test_update_proposal_not_found(self) -> None:
    """update_proposal() returns False when proposal not found."""
    session = Session.create()
    proposal = Proposal.create(session_id=session.session_id, text="test")

    result = session.update_proposal(proposal)

    assert result is False

  def test_multiple_proposals_maintain_order(self) -> None:
    """Proposals maintain insertion order."""
    session = Session.create()
    proposals = [
      Proposal.create(session_id=session.session_id, text=f"proposal {i}")
      for i in range(5)
    ]

    for p in proposals:
      session.add_proposal(p)

    for i, p in enumerate(session.proposals):
      assert p.text == f"proposal {i}"
