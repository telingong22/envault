"""Tests for envault.env_sort."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.vault import Vault
from envault.env_sort import SortError, SortResult, sort_keys

PASSPHRASE = "sort-secret"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    env.write_text("ZEBRA=1\nAPPLE=2\nMANGO=3\nBANANA=4\n")
    v = Vault(str(tmp_path / ".env"), passphrase=PASSPHRASE)
    vp = v.lock(env_path=str(env))
    return Path(vp)


# ---------------------------------------------------------------------------
# return type
# ---------------------------------------------------------------------------

def test_sort_returns_sort_result(vault_file):
    result = sort_keys(vault_file, PASSPHRASE)
    assert isinstance(result, SortResult)


def test_sort_result_contains_vault_path(vault_file):
    result = sort_keys(vault_file, PASSPHRASE)
    assert result.vault_path == vault_file


# ---------------------------------------------------------------------------
# sorted_order correctness
# ---------------------------------------------------------------------------

def test_sort_ascending_order(vault_file):
    result = sort_keys(vault_file, PASSPHRASE)
    assert result.sorted_order == sorted(result.original_order)


def test_sort_descending_order(vault_file):
    result = sort_keys(vault_file, PASSPHRASE, reverse=True)
    assert result.sorted_order == sorted(result.original_order, reverse=True)


def test_sort_changed_flag_true_when_reordered(vault_file):
    result = sort_keys(vault_file, PASSPHRASE)
    # ZEBRA comes first originally so ascending sort changes order
    assert result.changed is True


def test_sort_changed_flag_false_when_already_sorted(tmp_path):
    env = tmp_path / ".env"
    env.write_text("APPLE=1\nBANANA=2\nZEBRA=3\n")
    v = Vault(str(tmp_path / ".env"), passphrase=PASSPHRASE)
    vp = Path(v.lock(env_path=str(env)))
    result = sort_keys(vp, PASSPHRASE)
    assert result.changed is False


# ---------------------------------------------------------------------------
# custom key_order
# ---------------------------------------------------------------------------

def test_sort_custom_key_order(vault_file):
    explicit = ["MANGO", "ZEBRA"]
    result = sort_keys(vault_file, PASSPHRASE, key_order=explicit)
    # MANGO and ZEBRA must come first in that order
    assert result.sorted_order[:2] == ["MANGO", "ZEBRA"]


def test_sort_custom_order_remaining_keys_alphabetical(vault_file):
    explicit = ["MANGO"]
    result = sort_keys(vault_file, PASSPHRASE, key_order=explicit)
    rest = result.sorted_order[1:]
    assert rest == sorted(rest)


# ---------------------------------------------------------------------------
# persistence — vault is re-locked with sorted content
# ---------------------------------------------------------------------------

def test_sort_persists_in_vault(vault_file, tmp_path):
    sort_keys(vault_file, PASSPHRASE)
    v = Vault(str(vault_file.with_suffix("")), passphrase=PASSPHRASE)
    env_path = v.unlock(vault_path=vault_file)
    lines = [l for l in Path(env_path).read_text().splitlines() if "=" in l]
    keys = [l.split("=", 1)[0].strip() for l in lines]
    assert keys == sorted(keys)


# ---------------------------------------------------------------------------
# error handling
# ---------------------------------------------------------------------------

def test_sort_missing_vault_raises(tmp_path):
    with pytest.raises(SortError):
        sort_keys(tmp_path / "ghost.vault", PASSPHRASE)
