"""Integration tests for envault.vault.Vault."""

import pytest
from pathlib import Path

from envault.vault import Vault

PASSPHRASE = "vault-test-pass"
ENV_CONTENT = b"API_KEY=abc123\nSECRET=xyz\n"


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_bytes(ENV_CONTENT)
    return p


def test_lock_creates_vault_file(env_file: Path):
    vault = Vault(env_file)
    vault_path = vault.lock(PASSPHRASE)
    assert vault_path.exists()
    assert vault_path.suffix == ".vault"


def test_is_locked_after_lock(env_file: Path):
    vault = Vault(env_file)
    assert not vault.is_locked()
    vault.lock(PASSPHRASE)
    assert vault.is_locked()


def test_unlock_restores_content(env_file: Path, tmp_path: Path):
    vault = Vault(env_file)
    vault.lock(PASSPHRASE)
    output = tmp_path / ".env.restored"
    vault.unlock(PASSPHRASE, output_path=output)
    assert output.read_bytes() == ENV_CONTENT


def test_unlock_overwrites_env_by_default(env_file: Path):
    vault = Vault(env_file)
    vault.lock(PASSPHRASE)
    env_file.write_bytes(b"")  # simulate cleared file
    vault.unlock(PASSPHRASE)
    assert env_file.read_bytes() == ENV_CONTENT


def test_lock_missing_file_raises(tmp_path: Path):
    vault = Vault(tmp_path / "nonexistent.env")
    with pytest.raises(FileNotFoundError):
        vault.lock(PASSPHRASE)


def test_unlock_missing_vault_raises(env_file: Path):
    vault = Vault(env_file)
    with pytest.raises(FileNotFoundError):
        vault.unlock(PASSPHRASE)


def test_custom_vault_path(env_file: Path, tmp_path: Path):
    custom = tmp_path / "secrets.bin"
    vault = Vault(env_file, vault_path=custom)
    vault.lock(PASSPHRASE)
    assert custom.exists()
