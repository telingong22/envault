"""Tests for the snapshot CLI commands."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_snapshot import snapshot_group


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    vf = tmp_path / ".env.vault"
    vf.write_bytes(b"FAKEVAULTBYTES")
    return vf


def test_save_command_exits_ok(runner, vault_file, tmp_path):
    snap_dir = str(tmp_path / "snaps")
    result = runner.invoke(
        snapshot_group, ["save", str(vault_file), "--snapshot-dir", snap_dir]
    )
    assert result.exit_code == 0


def test_save_command_output_contains_snapshot(runner, vault_file, tmp_path):
    snap_dir = str(tmp_path / "snaps")
    result = runner.invoke(
        snapshot_group, ["save", str(vault_file), "--snapshot-dir", snap_dir]
    )
    assert "Snapshot saved" in result.output


def test_save_command_with_label(runner, vault_file, tmp_path):
    snap_dir = str(tmp_path / "snaps")
    result = runner.invoke(
        snapshot_group,
        ["save", str(vault_file), "--label", "release-1", "--snapshot-dir", snap_dir],
    )
    assert result.exit_code == 0
    assert "release-1" in result.output


def test_save_command_missing_vault(runner, tmp_path):
    snap_dir = str(tmp_path / "snaps")
    result = runner.invoke(
        snapshot_group,
        ["save", str(tmp_path / "ghost.vault"), "--snapshot-dir", snap_dir],
    )
    assert result.exit_code != 0


def test_list_command_no_snapshots(runner, tmp_path):
    snap_dir = str(tmp_path / "snaps")
    result = runner.invoke(snapshot_group, ["list", "--snapshot-dir", snap_dir])
    assert result.exit_code == 0
    assert "No snapshots" in result.output


def test_list_command_shows_entry(runner, vault_file, tmp_path):
    snap_dir = str(tmp_path / "snaps")
    runner.invoke(
        snapshot_group,
        ["save", str(vault_file), "--label", "mysnap", "--snapshot-dir", snap_dir],
    )
    result = runner.invoke(snapshot_group, ["list", "--snapshot-dir", snap_dir])
    assert "mysnap" in result.output


def test_restore_command_overwrites_target(runner, vault_file, tmp_path):
    snap_dir = str(tmp_path / "snaps")
    runner.invoke(
        snapshot_group, ["save", str(vault_file), "--snapshot-dir", snap_dir]
    )
    from envault.snapshot import list_snapshots
    entries = list_snapshots(snapshot_dir=Path(snap_dir))
    snap_path = entries[0]["snapshot"]

    target = tmp_path / "restored.vault"
    target.write_bytes(b"OLD")
    result = runner.invoke(snapshot_group, ["restore", snap_path, str(target)])
    assert result.exit_code == 0
    assert target.read_bytes() == vault_file.read_bytes()
