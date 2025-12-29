"""Type-safe broadcaster wrapper for betterproto messages.

This module provides a generic wrapper around the broadcaster library
that handles serialization/deserialization of betterproto messages,
ensuring type safety across the codebase.
"""

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, TypeVar

import betterproto
from broadcaster import Broadcast

if TYPE_CHECKING:
  from collections.abc import AsyncGenerator, AsyncIterator

# T must be a subclass of betterproto.Message
T = TypeVar("T", bound=betterproto.Message)


class ProtoBroadcaster[T: betterproto.Message]:
  """A strongly-typed wrapper around broadcaster.

  Automatically handles serialization (to JSON) and deserialization
  (back to the specific betterproto.Message class).

  Example:
      >>> from rpc_stream_prototype.generated.proposal.v1 import SessionEvent
      >>> broadcaster = ProtoBroadcaster("memory://", SessionEvent)
      >>> await broadcaster.connect()
      >>> async with broadcaster.subscribe("session-123") as stream:
      ...     await broadcaster.publish("session-123", event)
      ...     async for received_event in stream:
      ...         print(received_event)
  """

  def __init__(self, url: str, message_class: type[T]) -> None:
    """Initialize the broadcaster.

    Args:
        url: The backend URL (e.g., "memory://" for in-memory).
        message_class: The betterproto message class for deserialization.
    """
    self._backend = Broadcast(url)
    self._message_class = message_class

  async def connect(self) -> None:
    """Connect to the broadcast backend."""
    await self._backend.connect()

  async def disconnect(self) -> None:
    """Disconnect from the broadcast backend."""
    await self._backend.disconnect()

  async def publish(self, channel: str, message: T) -> None:
    """Publish a typed message to a channel.

    The message is serialized to JSON before publishing.

    Args:
        channel: The channel to publish to.
        message: The betterproto message to publish.
    """
    payload = message.to_json()
    await self._backend.publish(channel, payload)

  @asynccontextmanager
  async def subscribe(self, channel: str) -> AsyncGenerator[AsyncIterator[T]]:
    """Subscribe to a channel and receive typed messages.

    Args:
        channel: The channel to subscribe to.

    Yields:
        An async iterator of typed betterproto messages.

    Example:
        >>> async with broadcaster.subscribe("my-channel") as stream:
        ...     async for message in stream:
        ...         print(message)
    """
    async with self._backend.subscribe(channel) as subscriber:

      async def typed_stream() -> AsyncIterator[T]:
        # Note: broadcaster's Subscriber.__aiter__ has unusual return type annotation
        # (AsyncGenerator | None) that confuses type checkers, but works at runtime
        async for event in subscriber:  # type: ignore[union-attr]
          # Deserialize JSON back to the specific proto class
          yield self._message_class().from_json(event.message)  # type: ignore[misc]

      yield typed_stream()
