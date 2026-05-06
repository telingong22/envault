"""Tests for envault.diff module."""

import os
import pytest

from envault.diff import DiffResult, diff_envs, diff_files, diff_vault
from envault.vault import Vault


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("API_KEY=abc\nDEBUG=true\nHOST=localhost\n")
    return str(p)


@pytest.fixture()
def vault_file(tmp_path, env_file):
    vault_path = str(tmp_path / ".env.vault")
    v = Vault(vault_path)
    v.lock(env_file, passphrase="secret")
    return vault_path


# ---------------------------------------------------------------------------
# DiffResult unit tests
# ---------------------------------------------------------------------------

def test_diff_envs_added():
    left = {"A": "1"}
    right = {"A": "1", "B": "2"}
    result = diff_envs(left, right)
    assert "B" in result.added
    assert not result.removed


def test_diff_envs_removed():
    left = {"A": "1", "B": "2"}
    right = {"A": "1"}
    result = diff_envs(left, right)
    assert "B" in result.removed
    assert not result.added


def test_diff_envs_changed():
    left = {"A": "old"}
    right = {"A": "new"}
    result = diff_envs(left, right)
    assert "A" in result.changed
    assert not result.unchanged


def test_diff_envs_unchanged():
    left = {"A": "same"}
    right = {"A": "same"}
    result = diff_envs(left, right)
    assert "A" in result.unchanged
    assert not result.changed


def test_has_changes_true():
    r = DiffResult(added=["X"])
    assert r.has_changes is True


def test_has_changes_false():
    r = DiffResult(unchanged=["X"])
    assert r.has_changes is False


def test_summary_prefixes(tmp_path):
    r = DiffResult(added=["A"], removed=["B"], changed=["C"], unchanged=["D"])
    summary = r.summary()
    assert "+ A" in summary
    assert "- B" in summary
    assert "~ C" in summary
    assert "  D" in summary


# ---------------------------------------------------------------------------
# diff_files integration test
# ---------------------------------------------------------------------------

def test_diff_files(tmp_path):
    f1 = tmp_path / "a.env"
    f2 = tmp_path / "b.env"
    f1.write_text("KEY=1\nOLD=yes\n")
    f2.write_text("KEY=2\nNEW=no\n")
    result = diff_files(str(f1), str(f2))
    assert "KEY" in result.changed
    assert "OLD" in result.removed
    assert "NEW" in result.added


# ---------------------------------------------------------------------------
# diff_vault integration test
# ---------------------------------------------------------------------------

def test_diff_vault_no_changes(env_file, vault_file):
    result = diff_vault(env_file, vault_file, passphrase="secret")
    assert not result.has_changes


def test_diff_vault_detects_new_key(tmp_path, env_file, vault_file):
    # Add a new key to the live .env after locking
    with open(env_file, "a") as fh:
        fh.write("NEW_KEY=xyz\n")
    result = diff_vault(env_file, vault_file, passphrase="secret")
    assert "NEW_KEY" in result.added
