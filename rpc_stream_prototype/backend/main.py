"""Backend server entry point."""

import asyncio


async def serve() -> None:
  """Start the gRPC server."""
  print("Server starting on port 50051...")
  # Stub: actual implementation in PR #3
  while True:
    await asyncio.sleep(3600)


def main() -> None:
  """Entry point for rpc-server command."""
  asyncio.run(serve())


if __name__ == "__main__":
  main()
