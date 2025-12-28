"""Core CLI app setup."""

from __future__ import annotations

import structlog
import typer
from rich.console import Console
from structlog.typing import FilteringBoundLogger

from rpc_stream_prototype.logging_config import configure_logging

console = Console()


def get_logger() -> FilteringBoundLogger:
  """Configure logging and return a logger instance."""
  configure_logging()
  return structlog.get_logger()


app = typer.Typer(
  help="Proto-type of shared session communication using gRPC streaming",
  no_args_is_help=True,
)


@app.command()
def hello(name: str = "World"):
  """Say hello."""
  log = get_logger()
  log.info("saying_hello", name=name)
  console.print(f"Hello [bold blue]{name}[/bold blue]!")


if __name__ == "__main__":
  app()
