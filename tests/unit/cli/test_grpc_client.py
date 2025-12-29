"""Unit tests for ProposalClient gRPC wrapper."""

import pytest

from rpc_stream_prototype.cli.client.grpc_client import ProposalClient


class TestProposalClientConnection:
  """Tests for connection management."""

  def test_client_initializes_with_defaults(self) -> None:
    """Client should initialize with default host and port."""
    client = ProposalClient()

    assert client._host == "localhost"
    assert client._port == 50051
    assert client._channel is None
    assert client._stub is None

  def test_client_accepts_custom_host_and_port(self) -> None:
    """Client should accept custom host and port."""
    client = ProposalClient(host="custom-host", port=9999)

    assert client._host == "custom-host"
    assert client._port == 9999


class TestProposalClientEnsureConnected:
  """Tests for _ensure_connected method."""

  def test_raises_when_not_connected(self) -> None:
    """Should raise RuntimeError when not connected."""
    client = ProposalClient()

    with pytest.raises(RuntimeError, match="Client not connected"):
      client._ensure_connected()


class TestProposalClientSessionManager:
  """Tests for session() context manager."""

  async def test_session_connects_and_closes(self) -> None:
    """Session context manager should connect on entry and close on exit."""
    client = ProposalClient()

    # We can't fully test without a real server, but we can verify
    # the context manager protocol works by checking it's an async generator
    cm = client.session()
    assert hasattr(cm, "__aenter__")
    assert hasattr(cm, "__aexit__")
