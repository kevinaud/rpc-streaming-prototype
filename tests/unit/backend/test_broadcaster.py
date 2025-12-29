"""Unit tests for the event broadcaster."""

import asyncio

import pytest

from rpc_stream_prototype.backend.events.broadcaster import (
  EventBroadcaster,
  EventType,
  SessionEvent,
)
from rpc_stream_prototype.backend.models.domain import Proposal


class TestEventBroadcaster:
  """Tests for EventBroadcaster."""

  @pytest.fixture
  def broadcaster(self) -> EventBroadcaster:
    """Create a fresh broadcaster for each test."""
    return EventBroadcaster()

  @pytest.fixture
  def sample_proposal(self) -> Proposal:
    """Create a sample proposal for testing."""
    return Proposal.create(session_id="test-session", text="test proposal")

  @pytest.mark.asyncio
  async def test_subscribe_returns_queue(self, broadcaster: EventBroadcaster) -> None:
    """subscribe() returns an asyncio.Queue."""
    queue = await broadcaster.subscribe("session-123")

    assert isinstance(queue, asyncio.Queue)

  @pytest.mark.asyncio
  async def test_subscribe_increments_count(
    self, broadcaster: EventBroadcaster
  ) -> None:
    """subscribe() increases subscriber count."""
    assert await broadcaster.get_subscriber_count("session-123") == 0

    await broadcaster.subscribe("session-123")

    assert await broadcaster.get_subscriber_count("session-123") == 1

  @pytest.mark.asyncio
  async def test_multiple_subscribers(self, broadcaster: EventBroadcaster) -> None:
    """Multiple subscribers can subscribe to same session."""
    await broadcaster.subscribe("session-123")
    await broadcaster.subscribe("session-123")
    await broadcaster.subscribe("session-123")

    assert await broadcaster.get_subscriber_count("session-123") == 3

  @pytest.mark.asyncio
  async def test_unsubscribe_decrements_count(
    self, broadcaster: EventBroadcaster
  ) -> None:
    """unsubscribe() decreases subscriber count."""
    queue = await broadcaster.subscribe("session-123")

    await broadcaster.unsubscribe("session-123", queue)

    assert await broadcaster.get_subscriber_count("session-123") == 0

  @pytest.mark.asyncio
  async def test_unsubscribe_nonexistent_session(
    self, broadcaster: EventBroadcaster
  ) -> None:
    """unsubscribe() handles nonexistent session gracefully."""
    queue: asyncio.Queue[SessionEvent] = asyncio.Queue()

    # Should not raise
    await broadcaster.unsubscribe("nonexistent", queue)

  @pytest.mark.asyncio
  async def test_broadcast_delivers_to_subscriber(
    self, broadcaster: EventBroadcaster, sample_proposal: Proposal
  ) -> None:
    """broadcast() delivers event to subscribed queue."""
    queue = await broadcaster.subscribe("test-session")
    event = SessionEvent(
      session_id="test-session",
      event_type=EventType.PROPOSAL_CREATED,
      proposal=sample_proposal,
    )

    await broadcaster.broadcast(event)

    received = queue.get_nowait()
    assert received.session_id == "test-session"
    assert received.event_type == EventType.PROPOSAL_CREATED
    assert received.proposal == sample_proposal

  @pytest.mark.asyncio
  async def test_broadcast_delivers_to_all_subscribers(
    self, broadcaster: EventBroadcaster, sample_proposal: Proposal
  ) -> None:
    """broadcast() delivers event to all subscribers."""
    queues = [await broadcaster.subscribe("test-session") for _ in range(3)]
    event = SessionEvent(
      session_id="test-session",
      event_type=EventType.PROPOSAL_CREATED,
      proposal=sample_proposal,
    )

    await broadcaster.broadcast(event)

    for queue in queues:
      received = queue.get_nowait()
      assert received.event_type == EventType.PROPOSAL_CREATED

  @pytest.mark.asyncio
  async def test_broadcast_only_to_correct_session(
    self, broadcaster: EventBroadcaster, sample_proposal: Proposal
  ) -> None:
    """broadcast() only delivers to subscribers of the correct session."""
    queue1 = await broadcaster.subscribe("session-1")
    queue2 = await broadcaster.subscribe("session-2")

    event = SessionEvent(
      session_id="session-1",
      event_type=EventType.PROPOSAL_CREATED,
      proposal=sample_proposal,
    )
    await broadcaster.broadcast(event)

    assert not queue1.empty()
    assert queue2.empty()

  @pytest.mark.asyncio
  async def test_broadcast_proposal_updated_event(
    self, broadcaster: EventBroadcaster, sample_proposal: Proposal
  ) -> None:
    """broadcast() can deliver PROPOSAL_UPDATED events."""
    queue = await broadcaster.subscribe("test-session")
    updated_proposal = sample_proposal.approve()
    event = SessionEvent(
      session_id="test-session",
      event_type=EventType.PROPOSAL_UPDATED,
      proposal=updated_proposal,
    )

    await broadcaster.broadcast(event)

    received = queue.get_nowait()
    assert received.event_type == EventType.PROPOSAL_UPDATED

  @pytest.mark.asyncio
  async def test_broadcast_to_empty_session(
    self, broadcaster: EventBroadcaster, sample_proposal: Proposal
  ) -> None:
    """broadcast() handles session with no subscribers gracefully."""
    event = SessionEvent(
      session_id="empty-session",
      event_type=EventType.PROPOSAL_CREATED,
      proposal=sample_proposal,
    )

    # Should not raise
    await broadcaster.broadcast(event)

  @pytest.mark.asyncio
  async def test_unsubscribed_queue_stops_receiving(
    self, broadcaster: EventBroadcaster, sample_proposal: Proposal
  ) -> None:
    """After unsubscribe(), queue no longer receives events."""
    queue = await broadcaster.subscribe("test-session")
    await broadcaster.unsubscribe("test-session", queue)

    event = SessionEvent(
      session_id="test-session",
      event_type=EventType.PROPOSAL_CREATED,
      proposal=sample_proposal,
    )
    await broadcaster.broadcast(event)

    assert queue.empty()

  @pytest.mark.asyncio
  async def test_subscriber_count_different_sessions(
    self, broadcaster: EventBroadcaster
  ) -> None:
    """Subscriber counts are tracked per session."""
    await broadcaster.subscribe("session-1")
    await broadcaster.subscribe("session-1")
    await broadcaster.subscribe("session-2")

    assert await broadcaster.get_subscriber_count("session-1") == 2
    assert await broadcaster.get_subscriber_count("session-2") == 1
    assert await broadcaster.get_subscriber_count("session-3") == 0
