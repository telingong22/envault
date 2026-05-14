"""Tests for envault.env_redact."""
from __future__ import annotations

import pytest
from pathlib import Path

from envault.vault import Vault
from envault.env_redact import RedactError, RedactResult, redact_keys, _redact_lines

_PASSPHRASE = "test-passphrase"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    env.write_text("API_KEY=supersecret\nDB_PASS=hunter2\nAPP_NAME=myapp\n")
    v = Vault(tmp_path / ".env.vault")
    v.lock(_PASSPHRASE, env_file=env)
    env.unlink()
    return tmp_path / ".env.vault"


# --- unit tests for _redact_lines ---

def test_redact_lines_replaces_value():
    lines = ["API_KEY=supersecret\n", "APP=myapp\n"]
    new_lines, redacted, skipped = _redact_lines(lines, ["API_KEY"], "***")
    assert any("API_KEY=***" in l for l in new_lines)


def test_redact_lines_returns_redacted_key():
    lines = ["API_KEY=secret\n"]
    _, redacted, _ = _redact_lines(lines, ["API_KEY"], "***")
    assert "API_KEY" in redacted


def test_redact_lines_missing_key_goes_to_skipped():
    lines = ["APP=myapp\n"]
    _, redacted, skipped = _redact_lines(lines, ["MISSING"], "***")
    assert "MISSING" in skipped
    assert redacted == []


def test_redact_lines_preserves_comments():
    lines = ["# comment\n", "KEY=val\n"]
    new_lines, _, _ = _redact_lines(lines, ["KEY"], "***")
    assert new_lines[0] == "# comment\n"


def test_redact_lines_preserves_blank_lines():
    lines = ["\n", "KEY=val\n"]
    new_lines, _, _ = _redact_lines(lines, ["KEY"], "***")
    assert new_lines[0] == "\n"


# --- integration tests for redact_keys ---

def test_redact_returns_redact_result(vault_file: Path):
    result = redact_keys(vault_file, _PASSPHRASE, ["API_KEY"])
    assert isinstance(result, RedactResult)


def test_redact_result_contains_vault_path(vault_file: Path):
    result = redact_keys(vault_file, _PASSPHRASE, ["API_KEY"])
    assert result.vault_path == str(vault_file)


def test_redact_key_appears_in_redacted_list(vault_file: Path):
    result = redact_keys(vault_file, _PASSPHRASE, ["API_KEY"])
    assert "API_KEY" in result.redacted


def test_redact_missing_key_appears_in_skipped(vault_file: Path):
    result = redact_keys(vault_file, _PASSPHRASE, ["NONEXISTENT"])
    assert "NONEXISTENT" in result.skipped


def test_redact_has_changes_true_when_key_found(vault_file: Path):
    result = redact_keys(vault_file, _PASSPHRASE, ["DB_PASS"])
    assert result.has_changes() is True


def test_redact_has_changes_false_when_no_key_found(vault_file: Path):
    result = redact_keys(vault_file, _PASSPHRASE, ["GHOST_KEY"])
    assert result.has_changes() is False


def test_redacted_value_persists_after_unlock(vault_file: Path, tmp_path: Path):
    redact_keys(vault_file, _PASSPHRASE, ["API_KEY"])
    out = tmp_path / "out.env"
    v = Vault(vault_file)
    v.unlock(_PASSPHRASE, output=out)
    content = out.read_text()
    assert "***REDACTED***" in content
    assert "supersecret" not in content


def test_redact_custom_placeholder(vault_file: Path, tmp_path: Path):
    redact_keys(vault_file, _PASSPHRASE, ["DB_PASS"], placeholder="<hidden>")
    out = tmp_path / "out.env"
    Vault(vault_file).unlock(_PASSPHRASE, output=out)
    assert "<hidden>" in out.read_text()


def test_redact_missing_vault_raises(tmp_path: Path):
    with pytest.raises(RedactError, match="Vault not found"):
        redact_keys(tmp_path / "ghost.vault", _PASSPHRASE, ["KEY"])


def test_redact_empty_keys_raises(vault_file: Path):
    with pytest.raises(RedactError, match="No keys"):
        redact_keys(vault_file, _PASSPHRASE, [])


def test_as_dict_contains_expected_fields(vault_file: Path):
    result = redact_keys(vault_file, _PASSPHRASE, ["API_KEY", "MISSING"])
    d = result.as_dict()
    assert "vault_path" in d
    assert "redacted" in d
    assert "skipped" in d
    assert "has_changes" in d
