"""Server startup script."""

import asyncio

from grpclib.reflection.service import ServerReflection
from grpclib.server import Server
from grpclib.utils import graceful_exit

from rpc_stream_prototype.backend.services.approval_service import ApprovalService


async def main():
  # 1. Instantiate your services
  services = [ApprovalService()]

  # 2. Enable Reflection
  # This takes your list of services and adds the special Reflection service to it
  services = ServerReflection.extend(services)

  # 3. Create the server
  server = Server(services)
  host, port = "0.0.0.0", 50051

  print(f"Serving on {host}:{port} with Reflection enabled...")

  # 4. Start the server with graceful exit handling
  with graceful_exit([server]):
    await server.start(host, port)
    await server.wait_closed()


if __name__ == "__main__":
  asyncio.run(main())
