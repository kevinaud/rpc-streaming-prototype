"""CLI entry point."""

import typer

app = typer.Typer(help="Approver CLI for real-time approval workflow")


@app.command()
def start() -> None:
  """Start a new approval session."""
  print("CLI stub: start session")


@app.command()
def join(session_id: str) -> None:
  """Join an existing session."""
  print(f"CLI stub: join session {session_id}")


if __name__ == "__main__":
  app()
