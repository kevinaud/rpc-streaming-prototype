"""Unit tests for CLI display module."""

from io import StringIO
from unittest.mock import patch

from rpc_stream_prototype.cli.ui.display import (
  display_connected,
  display_decision_received,
  display_error,
  display_exit,
  display_info,
  display_proposal_sent,
  display_session_id,
  display_waiting_state,
)


class TestDisplaySessionId:
  """Tests for display_session_id function."""

  def test_displays_session_id(self) -> None:
    """Should display session ID in a panel."""
    with patch("sys.stdout", new_callable=StringIO):
      # Should not raise
      display_session_id("test-uuid-12345")


class TestDisplayConnected:
  """Tests for display_connected function."""

  def test_displays_connection_message(self) -> None:
    """Should display connection success message."""
    with patch("sys.stdout", new_callable=StringIO):
      # Should not raise
      display_connected("test-uuid-12345")


class TestDisplayWaitingState:
  """Tests for display_waiting_state function."""

  def test_displays_waiting_indicator(self) -> None:
    """Should display waiting indicator."""
    with patch("sys.stdout", new_callable=StringIO):
      # Should not raise
      display_waiting_state()


class TestDisplayProposalSent:
  """Tests for display_proposal_sent function."""

  def test_displays_proposal_confirmation(self) -> None:
    """Should display proposal sent confirmation."""
    with patch("sys.stdout", new_callable=StringIO):
      # Should not raise
      display_proposal_sent("proposal-123", "Test proposal text")


class TestDisplayDecisionReceived:
  """Tests for display_decision_received function."""

  def test_displays_approved(self) -> None:
    """Should display APPROVED for approved decision."""
    with patch("sys.stdout", new_callable=StringIO):
      # Should not raise
      display_decision_received(approved=True)

  def test_displays_rejected(self) -> None:
    """Should display REJECTED for rejected decision."""
    with patch("sys.stdout", new_callable=StringIO):
      # Should not raise
      display_decision_received(approved=False)


class TestDisplayError:
  """Tests for display_error function."""

  def test_displays_error_message(self) -> None:
    """Should display error message."""
    with patch("sys.stdout", new_callable=StringIO):
      # Should not raise
      display_error("Test error message")


class TestDisplayInfo:
  """Tests for display_info function."""

  def test_displays_info_message(self) -> None:
    """Should display informational message."""
    with patch("sys.stdout", new_callable=StringIO):
      # Should not raise
      display_info("Test info message")


class TestDisplayExit:
  """Tests for display_exit function."""

  def test_displays_exit_message(self) -> None:
    """Should display exit message."""
    with patch("sys.stdout", new_callable=StringIO):
      # Should not raise
      display_exit()
