"""Tests for envault.ttl."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from envault.ttl import TTLError, TTLRecord, clear_ttl, get_ttl, set_ttl
from envault.vault import Vault

PASSPHRASE = "test-pass"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    env.write_text("KEY=value\n", encoding="utf-8")
    v = Vault(env)
    return v.lock(PASSPHRASE)


def test_set_ttl_returns_ttl_record(vault_file: Path):
    record = set_ttl(vault_file, seconds=3600)
    assert isinstance(record, TTLRecord)


def test_set_ttl_creates_ttl_file(vault_file: Path):
    set_ttl(vault_file, seconds=3600)
    ttl_file = vault_file.with_suffix(".ttl.json")
    assert ttl_file.exists()


def test_set_ttl_file_is_json(vault_file: Path):
    import json
    set_ttl(vault_file, seconds=3600)
    ttl_file = vault_file.with_suffix(".ttl.json")
    data = json.loads(ttl_file.read_text())
    assert "expires_at" in data
    assert "expired" in data


def test_set_ttl_zero_raises(vault_file: Path):
    with pytest.raises(TTLError):
        set_ttl(vault_file, seconds=0)


def test_set_ttl_negative_raises(vault_file: Path):
    with pytest.raises(TTLError):
        set_ttl(vault_file, seconds=-10)


def test_set_ttl_missing_vault_raises(tmp_path: Path):
    with pytest.raises(TTLError):
        set_ttl(tmp_path / "nonexistent.vault", seconds=60)


def test_get_ttl_returns_record(vault_file: Path):
    set_ttl(vault_file, seconds=3600, note="ci")
    record = get_ttl(vault_file)
    assert isinstance(record, TTLRecord)
    assert record.note == "ci"


def test_get_ttl_not_expired_for_future(vault_file: Path):
    set_ttl(vault_file, seconds=3600)
    record = get_ttl(vault_file)
    assert not record.expired
    assert record.seconds_remaining > 0


def test_get_ttl_no_ttl_raises(vault_file: Path):
    with pytest.raises(TTLError):
        get_ttl(vault_file)


def test_clear_ttl_removes_file(vault_file: Path):
    set_ttl(vault_file, seconds=3600)
    result = clear_ttl(vault_file)
    assert result is True
    assert not vault_file.with_suffix(".ttl.json").exists()


def test_clear_ttl_returns_false_when_no_file(vault_file: Path):
    result = clear_ttl(vault_file)
    assert result is False


def test_as_dict_contains_expected_keys(vault_file: Path):
    record = set_ttl(vault_file, seconds=3600, note="deploy")
    d = record.as_dict()
    for key in ("vault_path", "expires_at", "note", "expired", "seconds_remaining"):
        assert key in d
