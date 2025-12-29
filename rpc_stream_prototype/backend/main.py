"""Server startup script for the approval workflow backend."""

import asyncio

from grpclib.reflection.service import ServerReflection
from grpclib.server import Server
from grpclib.utils import graceful_exit

from rpc_stream_prototype.backend.logging import configure_logging, get_logger
from rpc_stream_prototype.backend.services.proposal_service import ProposalService
from rpc_stream_prototype.backend.storage.session_store import SessionStore

logger = get_logger("main")


async def main() -> None:
  """Start the gRPC server with all services configured."""
  # Configure logging first
  configure_logging()

  # Initialize dependencies
  store = SessionStore()
  await store.connect()

  # Create the service with dependencies
  proposal_service = ProposalService(store)
  services = [proposal_service]

  # Enable Reflection for debugging tools like grpcurl
  services = ServerReflection.extend(services)

  # Create and start the server
  server = Server(services)
  host, port = "0.0.0.0", 50051

  logger.info("Starting server on %s:%d with Reflection enabled", host, port)
  print(f"Serving on {host}:{port} with Reflection enabled...")

  try:
    with graceful_exit([server]):
      await server.start(host, port)
      logger.info("Server started successfully")
      await server.wait_closed()
  finally:
    await store.disconnect()


if __name__ == "__main__":
  asyncio.run(main())
