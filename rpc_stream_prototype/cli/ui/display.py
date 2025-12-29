"""Display functions for CLI output."""

from rich.panel import Panel

from rpc_stream_prototype.cli.ui.console import console


def display_session_id(session_id: str) -> None:
  """Display session ID in a copyable format.

  Args:
    session_id: The session ID to display.
  """
  console.print(
    Panel(
      session_id,
      title="[bold green]Session Created[/bold green]",
      subtitle="Share this ID with Approvers",
      border_style="green",
    )
  )


def display_connected(session_id: str) -> None:
  """Display connection success message.

  Args:
    session_id: The session ID connected to.
  """
  short_id = session_id[:8]
  console.print(f"[green]✓ Connected to session {short_id}...[/green]")


def display_waiting_state() -> None:
  """Show waiting for decision indicator."""
  console.print("[dim]⏳ Waiting for decision...[/dim]")


def display_proposal_sent(proposal_id: str, text: str) -> None:
  """Display confirmation that proposal was sent.

  Args:
    proposal_id: The proposal ID.
    text: The proposal text.
  """
  short_id = proposal_id[:8]
  console.print(
    Panel(
      text,
      title=f"[bold blue]Proposal Sent[/bold blue] ({short_id}...)",
      border_style="blue",
    )
  )


def display_decision_received(approved: bool) -> None:
  """Display received decision.

  Args:
    approved: Whether the proposal was approved.
  """
  if approved:
    console.print("[bold green]✓ APPROVED[/bold green]")
  else:
    console.print("[bold red]✗ REJECTED[/bold red]")
  console.print()  # Empty line for spacing


def display_error(message: str) -> None:
  """Display an error message.

  Args:
    message: The error message to display.
  """
  console.print(f"[bold red]Error:[/bold red] {message}")


def display_info(message: str) -> None:
  """Display an informational message.

  Args:
    message: The message to display.
  """
  console.print(f"[dim]{message}[/dim]")


def display_exit() -> None:
  """Display exit message."""
  console.print("\n[dim]Exiting...[/dim]")
