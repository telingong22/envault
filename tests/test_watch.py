"""Tests for envault.watch."""

from __future__ import annotations

import time
import threading
from pathlib import Path

import pytest

from envault.watch import EnvWatcher, WatchError, WatchEvent, _file_digest
from envault.vault import Vault

PASSPHRASE = "watch-secret"


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("API_KEY=original\n")
    return p


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    return tmp_path / ".env.vault"


# ---------------------------------------------------------------------------
# Unit helpers
# ---------------------------------------------------------------------------

def test_file_digest_returns_string(env_file: Path) -> None:
    digest = _file_digest(env_file)
    assert isinstance(digest, str) and len(digest) == 64


def test_file_digest_missing_file(tmp_path: Path) -> None:
    assert _file_digest(tmp_path / "ghost.env") == ""


def test_file_digest_changes_on_write(env_file: Path) -> None:
    before = _file_digest(env_file)
    env_file.write_text("API_KEY=changed\n")
    after = _file_digest(env_file)
    assert before != after


# ---------------------------------------------------------------------------
# WatchEvent
# ---------------------------------------------------------------------------

def test_watch_event_as_dict(env_file: Path, vault_file: Path) -> None:
    evt = WatchEvent(env_path=env_file, vault_path=vault_file, change_detected_at=1.0, relocked=True)
    d = evt.as_dict()
    assert d["relocked"] is True
    assert d["env_path"] == str(env_file)


# ---------------------------------------------------------------------------
# EnvWatcher lifecycle
# ---------------------------------------------------------------------------

def test_watcher_starts_and_stops(env_file: Path, vault_file: Path) -> None:
    watcher = EnvWatcher(env_file, PASSPHRASE, vault_path=vault_file, interval=0.1)
    watcher.start()
    assert watcher.is_running()
    watcher.stop()
    assert not watcher.is_running()


def test_double_start_raises(env_file: Path, vault_file: Path) -> None:
    watcher = EnvWatcher(env_file, PASSPHRASE, vault_path=vault_file, interval=0.1)
    watcher.start()
    try:
        with pytest.raises(WatchError):
            watcher.start()
    finally:
        watcher.stop()


def test_watcher_relocks_on_change(env_file: Path, vault_file: Path) -> None:
    events: list[WatchEvent] = []
    watcher = EnvWatcher(
        env_file, PASSPHRASE, vault_path=vault_file,
        interval=0.05, on_event=events.append,
    )
    watcher.start()
    time.sleep(0.05)
    env_file.write_text("API_KEY=new_value\nSECRET=abc\n")
    deadline = time.time() + 2.0
    while not events and time.time() < deadline:
        time.sleep(0.05)
    watcher.stop()
    assert events, "Expected at least one watch event"
    assert events[0].relocked is True
    assert vault_file.exists()


def test_relocked_vault_is_readable(env_file: Path, vault_file: Path) -> None:
    env_file.write_text("TOKEN=secret\n")
    events: list[WatchEvent] = []
    watcher = EnvWatcher(
        env_file, PASSPHRASE, vault_path=vault_file,
        interval=0.05, on_event=events.append,
    )
    watcher.start()
    time.sleep(0.05)
    env_file.write_text("TOKEN=rotated\n")
    deadline = time.time() + 2.0
    while not events and time.time() < deadline:
        time.sleep(0.05)
    watcher.stop()
    restored = env_file.with_suffix(".restored")
    vault = Vault(restored, vault_file)
    vault.unlock(PASSPHRASE)
    assert "TOKEN" in restored.read_text()
