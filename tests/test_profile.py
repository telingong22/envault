"""Tests for envault.profile."""
import pytest
from pathlib import Path

from envault.profile import (
    ProfileError,
    create_profile,
    delete_profile,
    get_profile,
    list_profiles,
    _profiles_path,
)


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    vf = tmp_path / "test.vault"
    vf.write_bytes(b"dummy")
    return vf


def test_create_profile_returns_key_list(vault_file):
    keys = create_profile(vault_file, "prod", ["DB_URL", "SECRET_KEY"])
    assert keys == ["DB_URL", "SECRET_KEY"]


def test_create_profile_creates_json_file(vault_file):
    create_profile(vault_file, "prod", ["A"])
    assert _profiles_path(vault_file).exists()


def test_create_profile_deduplicates_keys(vault_file):
    keys = create_profile(vault_file, "prod", ["A", "B", "A"])
    assert keys == ["A", "B"]


def test_create_profile_empty_name_raises(vault_file):
    with pytest.raises(ProfileError):
        create_profile(vault_file, "", ["A"])


def test_get_profile_returns_keys(vault_file):
    create_profile(vault_file, "dev", ["FOO", "BAR"])
    assert get_profile(vault_file, "dev") == ["FOO", "BAR"]


def test_get_profile_missing_raises(vault_file):
    with pytest.raises(ProfileError, match="does not exist"):
        get_profile(vault_file, "ghost")


def test_list_profiles_empty(vault_file):
    assert list_profiles(vault_file) == {}


def test_list_profiles_multiple(vault_file):
    create_profile(vault_file, "prod", ["A"])
    create_profile(vault_file, "dev", ["B", "C"])
    profiles = list_profiles(vault_file)
    assert set(profiles.keys()) == {"prod", "dev"}


def test_delete_profile_removes_entry(vault_file):
    create_profile(vault_file, "staging", ["X"])
    delete_profile(vault_file, "staging")
    assert "staging" not in list_profiles(vault_file)


def test_delete_profile_missing_raises(vault_file):
    with pytest.raises(ProfileError, match="does not exist"):
        delete_profile(vault_file, "nope")


def test_create_profile_overwrites_existing(vault_file):
    create_profile(vault_file, "prod", ["OLD"])
    keys = create_profile(vault_file, "prod", ["NEW1", "NEW2"])
    assert keys == ["NEW1", "NEW2"]
    assert get_profile(vault_file, "prod") == ["NEW1", "NEW2"]
