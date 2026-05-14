"""Tests for envault.env_mask."""
from __future__ import annotations

import json

import pytest

from envault.env_mask import (
    MaskError,
    MaskResult,
    apply_masks,
    list_masked,
    mask_keys,
    unmask_keys,
    _mask_path,
)
from envault.vault import Vault


PASSPHRASE = "hunter2"


@pytest.fixture()
def vault_file(tmp_path):
    env = tmp_path / ".env"
    env.write_text("API_KEY=secret\nDEBUG=true\nDB_PASS=s3cr3t\n")
    v = Vault(env)
    vault = v.lock(PASSPHRASE)
    return vault


def test_mask_keys_returns_mask_result(vault_file):
    result = mask_keys(vault_file, PASSPHRASE, ["API_KEY"])
    assert isinstance(result, MaskResult)


def test_mask_keys_masked_list_contains_key(vault_file):
    result = mask_keys(vault_file, PASSPHRASE, ["API_KEY"])
    assert "API_KEY" in result.masked


def test_mask_keys_creates_masks_file(vault_file):
    mask_keys(vault_file, PASSPHRASE, ["API_KEY"])
    assert _mask_path(vault_file).exists()


def test_mask_keys_file_is_json(vault_file):
    mask_keys(vault_file, PASSPHRASE, ["API_KEY"])
    data = json.loads(_mask_path(vault_file).read_text())
    assert isinstance(data, list)


def test_mask_keys_persists(vault_file):
    mask_keys(vault_file, PASSPHRASE, ["API_KEY"])
    assert "API_KEY" in list_masked(vault_file)


def test_mask_multiple_keys(vault_file):
    mask_keys(vault_file, PASSPHRASE, ["API_KEY", "DB_PASS"])
    masked = list_masked(vault_file)
    assert "API_KEY" in masked
    assert "DB_PASS" in masked


def test_mask_duplicate_is_idempotent(vault_file):
    mask_keys(vault_file, PASSPHRASE, ["API_KEY"])
    mask_keys(vault_file, PASSPHRASE, ["API_KEY"])
    assert list_masked(vault_file).count("API_KEY") == 1


def test_unmask_keys_removes_key(vault_file):
    mask_keys(vault_file, PASSPHRASE, ["API_KEY", "DB_PASS"])
    unmask_keys(vault_file, PASSPHRASE, ["API_KEY"])
    assert "API_KEY" not in list_masked(vault_file)
    assert "DB_PASS" in list_masked(vault_file)


def test_unmask_returns_unmasked_list(vault_file):
    mask_keys(vault_file, PASSPHRASE, ["API_KEY"])
    result = unmask_keys(vault_file, PASSPHRASE, ["API_KEY"])
    assert "API_KEY" in result.unmasked


def test_unmask_nonexistent_key_empty_result(vault_file):
    result = unmask_keys(vault_file, PASSPHRASE, ["NONEXISTENT"])
    assert result.unmasked == []


def test_list_masked_empty_when_no_masks(vault_file):
    assert list_masked(vault_file) == []


def test_apply_masks_replaces_value(vault_file):
    mask_keys(vault_file, PASSPHRASE, ["API_KEY"])
    data = {"API_KEY": "secret", "DEBUG": "true"}
    result = apply_masks(data, vault_file)
    assert result["API_KEY"] == "***"
    assert result["DEBUG"] == "true"


def test_apply_masks_no_masks_unchanged(vault_file):
    data = {"API_KEY": "secret", "DEBUG": "true"}
    result = apply_masks(data, vault_file)
    assert result == data


def test_mask_missing_vault_raises(tmp_path):
    with pytest.raises(MaskError):
        mask_keys(tmp_path / "missing.vault", PASSPHRASE, ["KEY"])
