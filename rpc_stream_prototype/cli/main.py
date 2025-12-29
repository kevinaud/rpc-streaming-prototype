"""Proposer CLI entry point for real-time approval workflow."""

import asyncio
from typing import Annotated

import typer
from grpclib.client import Channel

from rpc_stream_prototype.cli.session.proposal_loop import run_proposal_loop
from rpc_stream_prototype.cli.ui.display import (
  display_connected,
  display_error,
  display_exit,
  display_session_id,
)
from rpc_stream_prototype.cli.ui.prompts import (
  prompt_session_action,
  prompt_session_id,
)
from rpc_stream_prototype.generated.proposal.v1 import (
  CreateSessionRequest,
  GetSessionRequest,
  ProposalServiceStub,
)

app = typer.Typer(help="Proposer CLI for real-time approval workflow")


@app.command()
def main(
  host: Annotated[str, typer.Option(help="Backend server host")] = "localhost",
  port: Annotated[int, typer.Option(help="Backend server port")] = 50051,
) -> None:
  """Start the Proposer CLI.

  Allows creating new sessions or continuing existing ones.
  Once connected, enter proposal text and wait for approval decisions.
  """
  try:
    asyncio.run(_main(host, port))
  except KeyboardInterrupt:
    display_exit()


async def _main(host: str, port: int) -> None:
  """Async main function for the CLI.

  Args:
    host: Backend server host.
    port: Backend server port.
  """
  channel = Channel(host, port)
  stub = ProposalServiceStub(channel)

  try:
    action = prompt_session_action()

    if action == "start":
      response = await stub.create_session(CreateSessionRequest())
      session_id = response.session.session_id
      display_session_id(session_id)
    else:
      session_id = prompt_session_id()
      try:
        await stub.get_session(GetSessionRequest(session_id=session_id))
        display_connected(session_id)
      except Exception:
        display_error("Session not found. Please check the ID and try again.")
        return

    await run_proposal_loop(stub, session_id)
  finally:
    channel.close()


if __name__ == "__main__":
  app()
