from typer.testing import CliRunner

from rpc_stream_prototype.cli.app import app

runner = CliRunner()


def test_hello():
  result = runner.invoke(app, ["hello", "--name", "Test"])
  assert result.exit_code == 0
  assert "Hello Test!" in result.stdout
