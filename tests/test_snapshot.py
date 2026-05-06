"""Tests for envault.snapshot."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.snapshot import (
    SnapshotError,
    list_snapshots,
    restore_snapshot,
    save_snapshot,
)


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    vf = tmp_path / ".env.vault"
    vf.write_bytes(b"FAKEVAULTDATA")
    return vf


@pytest.fixture()
def snap_dir(tmp_path: Path) -> Path:
    return tmp_path / "snaps"


def test_save_snapshot_returns_path(vault_file, snap_dir):
    snap = save_snapshot(vault_file, snapshot_dir=snap_dir)
    assert isinstance(snap, Path)
    assert snap.exists()


def test_save_snapshot_content_matches(vault_file, snap_dir):
    snap = save_snapshot(vault_file, snapshot_dir=snap_dir)
    assert snap.read_bytes() == vault_file.read_bytes()


def test_save_snapshot_filename_contains_label(vault_file, snap_dir):
    snap = save_snapshot(vault_file, label="myenv", snapshot_dir=snap_dir)
    assert "myenv" in snap.name


def test_save_snapshot_filename_contains_timestamp(vault_file, snap_dir):
    snap = save_snapshot(vault_file, snapshot_dir=snap_dir)
    # timestamp pattern: 8 digits T 6 digits Z
    import re
    assert re.search(r"\d{8}T\d{6}Z", snap.name)


def test_save_snapshot_raises_for_missing_vault(tmp_path, snap_dir):
    with pytest.raises(SnapshotError):
        save_snapshot(tmp_path / "nonexistent.vault", snapshot_dir=snap_dir)


def test_list_snapshots_empty_initially(snap_dir):
    assert list_snapshots(snapshot_dir=snap_dir) == []


def test_list_snapshots_after_save(vault_file, snap_dir):
    save_snapshot(vault_file, label="first", snapshot_dir=snap_dir)
    entries = list_snapshots(snapshot_dir=snap_dir)
    assert len(entries) == 1
    assert entries[0]["label"] == "first"


def test_list_snapshots_multiple(vault_file, snap_dir):
    save_snapshot(vault_file, label="a", snapshot_dir=snap_dir)
    save_snapshot(vault_file, label="b", snapshot_dir=snap_dir)
    entries = list_snapshots(snapshot_dir=snap_dir)
    assert len(entries) == 2


def test_restore_snapshot_overwrites_target(vault_file, snap_dir, tmp_path):
    snap = save_snapshot(vault_file, snapshot_dir=snap_dir)
    target = tmp_path / "restored.vault"
    target.write_bytes(b"OLD")
    restore_snapshot(snap, target)
    assert target.read_bytes() == vault_file.read_bytes()


def test_restore_snapshot_raises_for_missing(tmp_path):
    with pytest.raises(SnapshotError):
        restore_snapshot(tmp_path / "ghost.vault", tmp_path / "out.vault")
