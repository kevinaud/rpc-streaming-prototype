from typer.testing import CliRunner

from rpc_stream_prototype.cli.main import app

runner = CliRunner()


def test_start():
  """Test CLI start command."""
  result = runner.invoke(app, ["start"])
  assert result.exit_code == 0
  assert "start session" in result.stdout


def test_join():
  """Test CLI join command."""
  result = runner.invoke(app, ["join", "test-session-id"])
  assert result.exit_code == 0
  assert "join session test-session-id" in result.stdout
