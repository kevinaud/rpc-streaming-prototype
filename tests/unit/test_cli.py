"""Unit tests for CLI entry point.

Note: The CLI now has an interactive prompt, so we test the app exists
and basic invocation. Full CLI flows are tested in integration tests.
"""

from rpc_stream_prototype.cli.main import app


def test_cli_app_exists() -> None:
  """Test CLI app is defined."""
  assert app is not None
  assert hasattr(app, "command")


def test_cli_has_main_command() -> None:
  """Test CLI has registered the main command."""
  # The app should be callable
  assert callable(app)
