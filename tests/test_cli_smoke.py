from typer.testing import CliRunner

from healf_max.cli import app


def test_cli_imports_and_help_renders() -> None:
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Healf-Max" in result.output
    assert "kb" in result.output


def test_ask_degrades_without_openai_key(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("HEALF_MAX_DISABLE_DOTENV", "1")

    result = CliRunner().invoke(app, ["ask", "I need more energy"])

    assert result.exit_code == 0
    assert "OpenAI API key not configured" in result.output
    assert "not a bigger-stack moment" in result.output
