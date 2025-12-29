"""gRPC client wrapper for ProposalService."""

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Self

from grpclib.client import Channel

from rpc_stream_prototype.generated.proposal.v1 import (
  CreateSessionRequest,
  GetSessionRequest,
  ProposalServiceStub,
  SubmitProposalRequest,
  SubscribeRequest,
)

if TYPE_CHECKING:
  from collections.abc import AsyncIterator

  from rpc_stream_prototype.generated.proposal.v1 import (
    Proposal,
    SessionEvent,
  )


class ProposalClient:
  """Async gRPC client wrapper for ProposalService."""

  def __init__(self, host: str = "localhost", port: int = 50051) -> None:
    """Initialize the client.

    Args:
      host: Backend server host.
      port: Backend server port.
    """
    self._host = host
    self._port = port
    self._channel: Channel | None = None
    self._stub: ProposalServiceStub | None = None

  async def connect(self) -> None:
    """Connect to the gRPC server."""
    self._channel = Channel(self._host, self._port)
    self._stub = ProposalServiceStub(self._channel)

  async def close(self) -> None:
    """Close the gRPC channel."""
    if self._channel is not None:
      self._channel.close()
      self._channel = None
      self._stub = None

  @asynccontextmanager
  async def session(self) -> AsyncIterator[Self]:
    """Context manager for automatic connection handling."""
    await self.connect()
    try:
      yield self
    finally:
      await self.close()

  def _ensure_connected(self) -> ProposalServiceStub:
    """Ensure the client is connected and return the stub."""
    if self._stub is None:
      msg = (
        "Client not connected. Call connect() first or use session() context manager."
      )
      raise RuntimeError(msg)
    return self._stub

  async def create_session(self) -> str:
    """Create a new session and return the session ID.

    Returns:
      The newly created session ID.

    Raises:
      RuntimeError: If client is not connected.
      grpclib.GRPCError: If server request fails.
    """
    stub = self._ensure_connected()
    response = await stub.create_session(CreateSessionRequest())
    return response.session.session_id

  async def get_session(self, session_id: str) -> bool:
    """Check if a session exists.

    Args:
      session_id: The session ID to check.

    Returns:
      True if the session exists, False otherwise.
    """
    stub = self._ensure_connected()
    try:
      await stub.get_session(GetSessionRequest(session_id=session_id))
    except Exception:
      return False
    else:
      return True

  async def subscribe(
    self, session_id: str, client_id: str
  ) -> AsyncIterator[SessionEvent]:
    """Subscribe to session events.

    Args:
      session_id: The session ID to subscribe to.
      client_id: Unique identifier for this client.

    Yields:
      SessionEvent objects as they occur.
    """
    stub = self._ensure_connected()
    request = SubscribeRequest(session_id=session_id, client_id=client_id)
    async for response in stub.subscribe(request):
      yield response.event

  async def submit_proposal(self, session_id: str, text: str) -> Proposal:
    """Submit a proposal for approval.

    Args:
      session_id: The session ID to submit to.
      text: The proposal text.

    Returns:
      The created Proposal object.
    """
    stub = self._ensure_connected()
    request = SubmitProposalRequest(session_id=session_id, text=text)
    response = await stub.submit_proposal(request)
    return response.proposal
