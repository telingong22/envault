"""Tests for envault.backup."""
from __future__ import annotations

import time
from pathlib import Path

import pytest

from envault.backup import (
    BackupEntry,
    BackupError,
    create_backup,
    list_backups,
    prune_backups,
    restore_backup,
)


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    p = tmp_path / "secrets.vault"
    p.write_bytes(b"dummy-vault-content")
    return p


# --- create_backup ---

def test_create_backup_returns_backup_entry(vault_file):
    entry = create_backup(vault_file)
    assert isinstance(entry, BackupEntry)


def test_create_backup_file_exists(vault_file):
    entry = create_backup(vault_file)
    assert entry.path.exists()


def test_create_backup_content_matches(vault_file):
    entry = create_backup(vault_file)
    assert entry.path.read_bytes() == vault_file.read_bytes()


def test_create_backup_missing_vault_raises(tmp_path):
    with pytest.raises(BackupError):
        create_backup(tmp_path / "nonexistent.vault")


def test_create_backup_has_timestamp(vault_file):
    entry = create_backup(vault_file)
    assert len(entry.timestamp) == 15  # YYYYMMDD_HHMMSS


def test_create_backup_uses_bak_suffix(vault_file):
    entry = create_backup(vault_file)
    assert entry.path.suffix == ".bak"


# --- list_backups ---

def test_list_backups_empty_before_any(vault_file):
    assert list_backups(vault_file) == []


def test_list_backups_returns_entries(vault_file):
    create_backup(vault_file)
    time.sleep(0.01)
    create_backup(vault_file)
    entries = list_backups(vault_file)
    assert len(entries) == 2


def test_list_backups_newest_first(vault_file):
    create_backup(vault_file)
    time.sleep(1.1)  # ensure different second
    create_backup(vault_file)
    entries = list_backups(vault_file)
    assert entries[0].timestamp >= entries[1].timestamp


# --- restore_backup ---

def test_restore_backup_overwrites_vault(vault_file):
    entry = create_backup(vault_file)
    vault_file.write_bytes(b"changed")
    restore_backup(entry.path, vault_file)
    assert vault_file.read_bytes() == b"dummy-vault-content"


def test_restore_backup_missing_raises(vault_file):
    with pytest.raises(BackupError):
        restore_backup(vault_file.parent / "ghost.bak", vault_file)


# --- prune_backups ---

def test_prune_backups_removes_old(vault_file):
    for _ in range(4):
        create_backup(vault_file)
        time.sleep(0.01)
    removed = prune_backups(vault_file, keep=2)
    assert len(removed) == 2
    assert len(list_backups(vault_file)) == 2


def test_prune_backups_invalid_keep_raises(vault_file):
    with pytest.raises(BackupError):
        prune_backups(vault_file, keep=0)
