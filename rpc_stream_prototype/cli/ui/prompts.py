"""Interactive prompts for CLI user input."""

from rich.prompt import Prompt


def prompt_session_action() -> str:
  """Ask user to start new or continue existing session.

  Returns:
    Either "start" or "continue".
  """
  return Prompt.ask(
    "What would you like to do?",
    choices=["start", "continue"],
    default="start",
  )


def prompt_session_id() -> str:
  """Ask user for session ID to continue.

  Returns:
    The entered session ID.
  """
  return Prompt.ask("Enter Session ID")


def prompt_proposal_text() -> str:
  """Ask for proposal description.

  Returns:
    The entered proposal text (may be empty).
  """
  return Prompt.ask("Enter your proposal")
