"""Tests for envault.import_env and envault.cli_import."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_import import import_group
from envault.import_env import ImportError as EnvImportError
from envault.import_env import import_into_vault, _parse_dotenv, _parse_json
from envault.vault import Vault

PASSPHRASE = "s3cr3t"


@pytest.fixture()
def dotenv_source(tmp_path: Path) -> Path:
    p = tmp_path / "secrets.env"
    p.write_text('API_KEY=abc123\nDB_PASS="hunter2"\n# comment\n', encoding="utf-8")
    return p


@pytest.fixture()
def json_source(tmp_path: Path) -> Path:
    p = tmp_path / "secrets.json"
    p.write_text(json.dumps({"API_KEY": "abc123", "DB_PASS": "hunter2"}), encoding="utf-8")
    return p


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    return tmp_path / "my.vault"


# --- unit: _parse_dotenv ---

def test_parse_dotenv_returns_dict():
    result = _parse_dotenv('FOO=bar\nBAZ=qux\n')
    assert result == {"FOO": "bar", "BAZ": "qux"}


def test_parse_dotenv_strips_quotes():
    result = _parse_dotenv('FOO="hello world"\n')
    assert result["FOO"] == "hello world"


def test_parse_dotenv_ignores_comments():
    result = _parse_dotenv('# ignore me\nFOO=bar\n')
    assert "# ignore me" not in result
    assert result["FOO"] == "bar"


# --- unit: _parse_json ---

def test_parse_json_returns_dict():
    result = _parse_json('{"X": "1", "Y": "2"}')
    assert result == {"X": "1", "Y": "2"}


def test_parse_json_invalid_raises():
    with pytest.raises(EnvImportError, match="Invalid JSON"):
        _parse_json("not json")


def test_parse_json_non_object_raises():
    with pytest.raises(EnvImportError, match="object"):
        _parse_json('["a", "b"]')


# --- integration: import_into_vault ---

def test_import_dotenv_creates_vault(dotenv_source, vault_file):
    import_into_vault(dotenv_source, vault_file, PASSPHRASE, fmt="dotenv")
    assert vault_file.exists()


def test_import_dotenv_returns_dict(dotenv_source, vault_file):
    result = import_into_vault(dotenv_source, vault_file, PASSPHRASE, fmt="dotenv")
    assert isinstance(result, dict)
    assert result["API_KEY"] == "abc123"


def test_import_json_creates_vault(json_source, vault_file):
    result = import_into_vault(json_source, vault_file, PASSPHRASE, fmt="json")
    assert result["DB_PASS"] == "hunter2"


def test_import_missing_source_raises(vault_file, tmp_path):
    with pytest.raises(EnvImportError, match="not found"):
        import_into_vault(tmp_path / "nope.env", vault_file, PASSPHRASE)


def test_import_unsupported_format_raises(dotenv_source, vault_file):
    with pytest.raises(EnvImportError, match="Unsupported format"):
        import_into_vault(dotenv_source, vault_file, PASSPHRASE, fmt="xml")


def test_import_merge_preserves_existing_keys(tmp_path, vault_file):
    # Create initial vault with BASE_KEY
    initial = tmp_path / "initial.env"
    initial.write_text("BASE_KEY=original\n", encoding="utf-8")
    import_into_vault(initial, vault_file, PASSPHRASE)

    # Merge new key
    new_source = tmp_path / "new.env"
    new_source.write_text("NEW_KEY=added\n", encoding="utf-8")
    result = import_into_vault(new_source, vault_file, PASSPHRASE, merge=True)

    assert result["BASE_KEY"] == "original"
    assert result["NEW_KEY"] == "added"


# --- CLI ---

@pytest.fixture()
def runner():
    return CliRunner()


def test_cli_run_exits_ok(runner, dotenv_source, vault_file):
    result = runner.invoke(
        import_group,
        ["run", str(dotenv_source), "--vault", str(vault_file), "--passphrase", PASSPHRASE],
    )
    assert result.exit_code == 0


def test_cli_run_output_contains_count(runner, dotenv_source, vault_file):
    result = runner.invoke(
        import_group,
        ["run", str(dotenv_source), "--vault", str(vault_file), "--passphrase", PASSPHRASE],
    )
    assert "2" in result.output  # API_KEY + DB_PASS


def test_cli_run_merge_flag(runner, tmp_path, vault_file):
    src1 = tmp_path / "a.env"
    src1.write_text("ALPHA=1\n", encoding="utf-8")
    runner.invoke(
        import_group,
        ["run", str(src1), "--vault", str(vault_file), "--passphrase", PASSPHRASE],
    )
    src2 = tmp_path / "b.env"
    src2.write_text("BETA=2\n", encoding="utf-8")
    result = runner.invoke(
        import_group,
        ["run", str(src2), "--vault", str(vault_file), "--passphrase", PASSPHRASE, "--merge"],
    )
    assert result.exit_code == 0
    assert "Merged" in result.output
