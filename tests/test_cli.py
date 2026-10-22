from typer.testing import CliRunner
from flbds.cli import app

runner = CliRunner()

def test_cli_doctor():
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "FLBDS v3.0 System Self-Check" in result.output

def test_cli_validate_seed():
    result = runner.invoke(app, ["validate", "flbds/data/seeds/bio_lotus-self-cleaning.json"])
    assert result.exit_code == 0
    assert "PASS" in result.output
