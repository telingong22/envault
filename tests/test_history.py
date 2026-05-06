"""Tests for envault.history."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.history import (
    record,
    read_history,
    last_operation,
    clear_history,
    HistoryEntry,
)


@pytest.fixture
def vault_file(tmp_path: Path) -> Path:
    vf = tmp_path / "test.vault"
    vf.write_bytes(b"dummy")
    return vf


def test_record_returns_history_entry(vault_file):
    entry = record(vault_file, "lock")
    assert isinstance(entry, HistoryEntry)


def test_record_stores_operation(vault_file):
    entry = record(vault_file, "unlock")
    assert entry.operation == "unlock"


def test_record_stores_vault_path(vault_file):
    entry = record(vault_file, "lock")
    assert entry.vault_path == str(vault_file)


def test_record_timestamp_is_iso(vault_file):
    entry = record(vault_file, "lock")
    # Should not raise
    from datetime import datetime
    datetime.fromisoformat(entry.timestamp)


def test_record_extra_kwargs_stored(vault_file):
    entry = record(vault_file, "rotate", user="alice")
    assert entry.extra.get("user") == "alice"


def test_history_file_created(vault_file):
    record(vault_file, "lock")
    hist_file = vault_file.with_suffix(".history")
    assert hist_file.exists()


def test_history_file_is_ndjson(vault_file):
    record(vault_file, "lock")
    hist_file = vault_file.with_suffix(".history")
    for line in hist_file.read_text().splitlines():
        json.loads(line)  # must not raise


def test_read_history_empty_when_no_file(vault_file):
    assert read_history(vault_file) == []


def test_read_history_returns_all_entries(vault_file):
    record(vault_file, "lock")
    record(vault_file, "unlock")
    record(vault_file, "rotate")
    entries = read_history(vault_file)
    assert len(entries) == 3


def test_read_history_order_is_oldest_first(vault_file):
    record(vault_file, "lock")
    record(vault_file, "unlock")
    entries = read_history(vault_file)
    assert entries[0].operation == "lock"
    assert entries[1].operation == "unlock"


def test_last_operation_none_when_empty(vault_file):
    assert last_operation(vault_file) is None


def test_last_operation_returns_most_recent(vault_file):
    record(vault_file, "lock")
    record(vault_file, "rotate")
    entry = last_operation(vault_file)
    assert entry.operation == "rotate"


def test_clear_history_returns_count(vault_file):
    record(vault_file, "lock")
    record(vault_file, "unlock")
    count = clear_history(vault_file)
    assert count == 2


def test_clear_history_removes_file(vault_file):
    record(vault_file, "lock")
    clear_history(vault_file)
    hist_file = vault_file.with_suffix(".history")
    assert not hist_file.exists()


def test_clear_history_zero_when_no_file(vault_file):
    assert clear_history(vault_file) == 0
