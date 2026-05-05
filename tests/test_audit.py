"""Tests for envault.audit module."""

import json
from pathlib import Path

import pytest

from envault.audit import record_event, read_log, last_event, AUDIT_LOG_FILENAME


@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    return tmp_path / AUDIT_LOG_FILENAME


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("KEY=value\n")
    return p


def test_record_event_creates_log(env_file, log_file):
    record_event("lock", env_file, env_file.with_suffix(".vault"), log_path=log_file)
    assert log_file.exists()


def test_record_event_returns_dict(env_file, log_file):
    entry = record_event("lock", env_file, env_file.with_suffix(".vault"), log_path=log_file)
    assert entry["action"] == "lock"
    assert entry["success"] is True
    assert "timestamp" in entry


def test_multiple_events_appended(env_file, log_file):
    record_event("lock", env_file, env_file.with_suffix(".vault"), log_path=log_file)
    record_event("unlock", env_file, env_file.with_suffix(".vault"), log_path=log_file)
    events = read_log(log_file)
    assert len(events) == 2
    assert events[0]["action"] == "lock"
    assert events[1]["action"] == "unlock"


def test_read_log_missing_file_returns_empty(tmp_path):
    missing = tmp_path / "no_such_log.json"
    assert read_log(missing) == []


def test_read_log_corrupt_file_returns_empty(log_file):
    log_file.write_text("not json", encoding="utf-8")
    assert read_log(log_file) == []


def test_last_event_returns_most_recent(env_file, log_file):
    record_event("lock", env_file, env_file.with_suffix(".vault"), log_path=log_file)
    record_event("unlock", env_file, env_file.with_suffix(".vault"), log_path=log_file)
    entry = last_event(log_file)
    assert entry["action"] == "unlock"


def test_last_event_filtered_by_action(env_file, log_file):
    record_event("lock", env_file, env_file.with_suffix(".vault"), log_path=log_file)
    record_event("unlock", env_file, env_file.with_suffix(".vault"), log_path=log_file)
    record_event("lock", env_file, env_file.with_suffix(".vault"), log_path=log_file)
    entry = last_event(log_file, action="unlock")
    assert entry is not None
    assert entry["action"] == "unlock"


def test_last_event_none_when_empty(log_file):
    assert last_event(log_file) is None


def test_record_event_with_detail(env_file, log_file):
    record_event("lock", env_file, env_file.with_suffix(".vault"), log_path=log_file, detail="test run")
    entry = last_event(log_file)
    assert entry["detail"] == "test run"


def test_failed_event_recorded(env_file, log_file):
    record_event("unlock", env_file, env_file.with_suffix(".vault"), log_path=log_file, success=False, detail="bad passphrase")
    entry = last_event(log_file)
    assert entry["success"] is False
