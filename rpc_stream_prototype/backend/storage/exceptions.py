"""Storage layer exceptions.

These exceptions provide clear, specific error information from the storage
layer, allowing callers to handle failures appropriately without guessing
what went wrong.
"""


class StorageError(Exception):
  """Base exception for storage operations."""

  pass


class SessionNotFoundError(StorageError):
  """Raised when a session does not exist.

  Attributes:
      session_id: The ID of the session that was not found.
  """

  def __init__(self, session_id: str) -> None:
    self.session_id = session_id
    super().__init__(f"Session not found: {session_id}")


class ProposalNotFoundError(StorageError):
  """Raised when a proposal does not exist within a session.

  Attributes:
      session_id: The session that was searched.
      proposal_id: The ID of the proposal that was not found.
  """

  def __init__(self, session_id: str, proposal_id: str) -> None:
    self.session_id = session_id
    self.proposal_id = proposal_id
    super().__init__(f"Proposal not found: {proposal_id} in session {session_id}")
