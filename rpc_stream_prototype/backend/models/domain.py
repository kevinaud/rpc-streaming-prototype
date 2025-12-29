"""Internal domain models for the approval workflow.

These models are separate from the generated protobuf types to allow
for internal business logic and validation.
"""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


class ProposalStatus(Enum):
  """Status of a proposal in the workflow."""

  PENDING = "pending"
  APPROVED = "approved"
  REJECTED = "rejected"


@dataclass
class Proposal:
  """A proposal submitted for approval.

  Attributes:
      proposal_id: Unique identifier for this proposal.
      session_id: The session this proposal belongs to.
      text: The text content of the proposal.
      status: Current status of the proposal.
      created_at: Timestamp when the proposal was created.
  """

  proposal_id: str
  session_id: str
  text: str
  status: ProposalStatus = ProposalStatus.PENDING
  created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

  @classmethod
  def create(cls, session_id: str, text: str) -> Proposal:
    """Factory method to create a new proposal with generated ID.

    Args:
        session_id: The session this proposal belongs to.
        text: The text content of the proposal.

    Returns:
        A new Proposal instance with PENDING status.
    """
    return cls(
      proposal_id=str(uuid.uuid4()),
      session_id=session_id,
      text=text,
      status=ProposalStatus.PENDING,
      created_at=datetime.now(UTC),
    )

  def approve(self) -> Proposal:
    """Mark this proposal as approved.

    Returns:
        A new Proposal instance with APPROVED status.
    """
    return Proposal(
      proposal_id=self.proposal_id,
      session_id=self.session_id,
      text=self.text,
      status=ProposalStatus.APPROVED,
      created_at=self.created_at,
    )

  def reject(self) -> Proposal:
    """Mark this proposal as rejected.

    Returns:
        A new Proposal instance with REJECTED status.
    """
    return Proposal(
      proposal_id=self.proposal_id,
      session_id=self.session_id,
      text=self.text,
      status=ProposalStatus.REJECTED,
      created_at=self.created_at,
    )


@dataclass
class Session:
  """An approval session containing proposals.

  Attributes:
      session_id: Unique identifier for this session.
      proposals: List of proposals in this session.
      created_at: Timestamp when the session was created.
  """

  session_id: str
  proposals: list[Proposal] = field(default_factory=list)
  created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

  @classmethod
  def create(cls) -> Session:
    """Factory method to create a new session with generated ID.

    Returns:
        A new Session instance with empty proposals list.
    """
    return cls(
      session_id=str(uuid.uuid4()),
      proposals=[],
      created_at=datetime.now(UTC),
    )

  def get_pending_proposals(self) -> list[Proposal]:
    """Get all proposals with PENDING status.

    Returns:
        List of pending proposals.
    """
    return [p for p in self.proposals if p.status == ProposalStatus.PENDING]

  def get_proposal(self, proposal_id: str) -> Proposal | None:
    """Get a proposal by its ID.

    Args:
        proposal_id: The proposal ID to find.

    Returns:
        The proposal if found, None otherwise.
    """
    for proposal in self.proposals:
      if proposal.proposal_id == proposal_id:
        return proposal
    return None

  def add_proposal(self, proposal: Proposal) -> None:
    """Add a proposal to this session.

    Args:
        proposal: The proposal to add.
    """
    self.proposals.append(proposal)

  def update_proposal(self, updated_proposal: Proposal) -> bool:
    """Update a proposal in this session.

    Args:
        updated_proposal: The updated proposal (must have matching proposal_id).

    Returns:
        True if the proposal was found and updated, False otherwise.
    """
    for i, proposal in enumerate(self.proposals):
      if proposal.proposal_id == updated_proposal.proposal_id:
        self.proposals[i] = updated_proposal
        return True
    return False
