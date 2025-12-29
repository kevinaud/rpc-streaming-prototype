"""Unit tests for the ProtoBroadcaster."""

from typing import TYPE_CHECKING

import pytest

from rpc_stream_prototype.backend.events.proto_broadcaster import ProtoBroadcaster
from rpc_stream_prototype.generated.proposal.v1 import (
  Proposal,
  ProposalStatus,
  SessionEvent,
)

if TYPE_CHECKING:
  from collections.abc import AsyncGenerator


class TestProtoBroadcaster:
  """Tests for ProtoBroadcaster."""

  @pytest.fixture
  async def broadcaster(
    self,
  ) -> AsyncGenerator[ProtoBroadcaster[SessionEvent]]:
    """Create a connected broadcaster for each test."""
    _broadcaster = ProtoBroadcaster("memory://", SessionEvent)
    await _broadcaster.connect()
    yield _broadcaster
    await _broadcaster.disconnect()

  @pytest.fixture
  def sample_proposal(self) -> Proposal:
    """Create a sample proposal for testing."""
    return Proposal(
      proposal_id="test-proposal-id",
      text="Test proposal text",
      status=ProposalStatus.PENDING,
    )

  @pytest.fixture
  def sample_event(self, sample_proposal: Proposal) -> SessionEvent:
    """Create a sample session event for testing."""
    return SessionEvent(proposal_created=sample_proposal)

  @pytest.mark.asyncio
  async def test_publish_and_subscribe(
    self, broadcaster: ProtoBroadcaster[SessionEvent], sample_event: SessionEvent
  ) -> None:
    """Published messages are received by subscribers."""
    received_events: list[SessionEvent] = []

    async with broadcaster.subscribe("test-channel") as stream:
      # Publish in background
      await broadcaster.publish("test-channel", sample_event)

      async for event in stream:
        received_events.append(event)
        break  # Just get one event

    assert len(received_events) == 1
    assert received_events[0].proposal_created.proposal_id == "test-proposal-id"
    assert received_events[0].proposal_created.text == "Test proposal text"

  @pytest.mark.asyncio
  async def test_multiple_messages(
    self, broadcaster: ProtoBroadcaster[SessionEvent], sample_proposal: Proposal
  ) -> None:
    """Multiple messages are received in order."""
    events_to_send = [
      SessionEvent(
        proposal_created=Proposal(
          proposal_id=f"proposal-{i}",
          text=f"Proposal {i}",
          status=ProposalStatus.PENDING,
        )
      )
      for i in range(3)
    ]

    received_events: list[SessionEvent] = []

    async with broadcaster.subscribe("test-channel") as stream:
      for event in events_to_send:
        await broadcaster.publish("test-channel", event)

      count = 0
      async for event in stream:
        received_events.append(event)
        count += 1
        if count >= 3:
          break

    assert len(received_events) == 3
    for i, event in enumerate(received_events):
      assert event.proposal_created.proposal_id == f"proposal-{i}"

  @pytest.mark.asyncio
  async def test_different_channels(
    self, broadcaster: ProtoBroadcaster[SessionEvent], sample_proposal: Proposal
  ) -> None:
    """Messages are only received on subscribed channels."""
    event1 = SessionEvent(
      proposal_created=Proposal(
        proposal_id="channel1-proposal",
        text="Channel 1",
        status=ProposalStatus.PENDING,
      )
    )
    event2 = SessionEvent(
      proposal_created=Proposal(
        proposal_id="channel2-proposal",
        text="Channel 2",
        status=ProposalStatus.PENDING,
      )
    )

    received_events: list[SessionEvent] = []

    async with broadcaster.subscribe("channel1") as stream:
      # Publish to different channels
      await broadcaster.publish("channel1", event1)
      await broadcaster.publish("channel2", event2)

      # Only expect one message from channel1
      async for event in stream:
        received_events.append(event)
        break

    assert len(received_events) == 1
    assert received_events[0].proposal_created.proposal_id == "channel1-proposal"

  @pytest.mark.asyncio
  async def test_proposal_updated_event(
    self, broadcaster: ProtoBroadcaster[SessionEvent]
  ) -> None:
    """proposal_updated events are properly serialized."""
    event = SessionEvent(
      proposal_updated=Proposal(
        proposal_id="updated-proposal",
        text="Updated text",
        status=ProposalStatus.APPROVED,
      )
    )

    received_events: list[SessionEvent] = []

    async with broadcaster.subscribe("test-channel") as stream:
      await broadcaster.publish("test-channel", event)

      async for received in stream:
        received_events.append(received)
        break

    assert len(received_events) == 1
    assert received_events[0].proposal_updated.proposal_id == "updated-proposal"
    assert received_events[0].proposal_updated.status == ProposalStatus.APPROVED
