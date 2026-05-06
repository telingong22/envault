"""Tests for envault.export module."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.export import ExportError, export_vault
from envault.vault import Vault

PASSPHRASE = "test-secret-123"
ENV_CONTENT = 'DB_HOST=localhost\nDB_PORT=5432\nAPI_KEY="my key with spaces"\n'


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    env.write_text(ENV_CONTENT, encoding="utf-8")
    vault = tmp_path / ".env.vault"
    v = Vault(env_path=env, vault_path=vault)
    v.lock(PASSPHRASE)
    return vault


def test_export_dotenv_returns_string(vault_file: Path) -> None:
    result = export_vault(vault_file, PASSPHRASE, fmt="dotenv")
    assert isinstance(result, str)


def test_export_dotenv_contains_keys(vault_file: Path) -> None:
    result = export_vault(vault_file, PASSPHRASE, fmt="dotenv")
    assert "DB_HOST" in result
    assert "DB_PORT" in result
    assert "API_KEY" in result


def test_export_dotenv_contains_values(vault_file: Path) -> None:
    result = export_vault(vault_file, PASSPHRASE, fmt="dotenv")
    assert "localhost" in result
    assert "5432" in result


def test_export_json_is_valid_json(vault_file: Path) -> None:
    result = export_vault(vault_file, PASSPHRASE, fmt="json")
    data = json.loads(result)
    assert data["DB_HOST"] == "localhost"
    assert data["DB_PORT"] == "5432"


def test_export_shell_has_export_prefix(vault_file: Path) -> None:
    result = export_vault(vault_file, PASSPHRASE, fmt="shell")
    for line in result.strip().splitlines():
        assert line.startswith("export ")


def test_export_shell_values_single_quoted(vault_file: Path) -> None:
    result = export_vault(vault_file, PASSPHRASE, fmt="shell")
    assert "export DB_HOST='localhost'" in result


def test_export_writes_to_file(vault_file: Path, tmp_path: Path) -> None:
    out = tmp_path / "exported.env"
    export_vault(vault_file, PASSPHRASE, fmt="dotenv", output_path=out)
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "DB_HOST" in content


def test_export_unknown_format_raises(vault_file: Path) -> None:
    with pytest.raises(ExportError, match="Unknown format"):
        export_vault(vault_file, PASSPHRASE, fmt="xml")  # type: ignore[arg-type]


def test_export_missing_vault_raises(tmp_path: Path) -> None:
    with pytest.raises(ExportError, match="not found"):
        export_vault(tmp_path / "nonexistent.vault", PASSPHRASE)
