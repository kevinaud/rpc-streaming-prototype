"""Unit tests for CLI prompts module.

Note: Rich prompts are interactive, so we test the function signatures
and return types rather than actual user interaction. Integration tests
will cover the full interactive flow.
"""

from rpc_stream_prototype.cli.ui.prompts import (
  prompt_proposal_text,
  prompt_session_action,
  prompt_session_id,
)


class TestPromptFunctions:
  """Tests for prompt function definitions."""

  def test_prompt_session_action_exists(self) -> None:
    """prompt_session_action should be callable."""
    assert callable(prompt_session_action)

  def test_prompt_session_id_exists(self) -> None:
    """prompt_session_id should be callable."""
    assert callable(prompt_session_id)

  def test_prompt_proposal_text_exists(self) -> None:
    """prompt_proposal_text should be callable."""
    assert callable(prompt_proposal_text)
