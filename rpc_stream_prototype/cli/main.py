"""Proposer CLI entry point for real-time approval workflow."""

import asyncio
from typing import Annotated

import typer

from rpc_stream_prototype.cli.client.grpc_client import ProposalClient
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
  client = ProposalClient(host, port)

  async with client.session():
    action = prompt_session_action()

    if action == "start":
      session_id = await client.create_session()
      display_session_id(session_id)
    else:
      session_id = prompt_session_id()
      if not await client.get_session(session_id):
        display_error("Session not found. Please check the ID and try again.")
        return
      display_connected(session_id)

    await run_proposal_loop(client, session_id)


if __name__ == "__main__":
  app()
