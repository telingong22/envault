"""Tests for envault.env_cast."""
from __future__ import annotations

from pathlib import Path

import pytest

from envault.vault import Vault
from envault.env_cast import CastError, CastResult, _cast_value, cast_keys


PASSPHRASE = "hunter2"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    env.write_text(
        "PORT=8080\n"
        "RATE=3.14\n"
        "DEBUG=true\n"
        "NAME=envault\n"
        "EMPTY=\n"
    )
    v = Vault(tmp_path / ".env.vault")
    v.lock(env, PASSPHRASE)
    return tmp_path / ".env.vault"


# --- unit tests for _cast_value ---

def test_cast_int_valid():
    assert _cast_value("42", "int") == 42


def test_cast_int_invalid():
    with pytest.raises(CastError):
        _cast_value("abc", "int")


def test_cast_float_valid():
    assert _cast_value("3.14", "float") == pytest.approx(3.14)


def test_cast_float_invalid():
    with pytest.raises(CastError):
        _cast_value("nope", "float")


def test_cast_bool_true_variants():
    for val in ("1", "true", "yes", "on", "TRUE", "Yes"):
        assert _cast_value(val, "bool") is True


def test_cast_bool_false_variants():
    for val in ("0", "false", "no", "off", "FALSE"):
        assert _cast_value(val, "bool") is False


def test_cast_bool_invalid():
    with pytest.raises(CastError):
        _cast_value("maybe", "bool")


def test_cast_str_passthrough():
    assert _cast_value("hello", "str") == "hello"


def test_cast_unknown_type_raises():
    with pytest.raises(CastError, match="Unknown type"):
        _cast_value("x", "list")


# --- integration tests for cast_keys ---

def test_cast_keys_returns_cast_result(vault_file: Path):
    result = cast_keys(vault_file, PASSPHRASE, {"PORT": "int"})
    assert isinstance(result, CastResult)


def test_cast_keys_int(vault_file: Path):
    result = cast_keys(vault_file, PASSPHRASE, {"PORT": "int"})
    assert result.values["PORT"] == 8080


def test_cast_keys_float(vault_file: Path):
    result = cast_keys(vault_file, PASSPHRASE, {"RATE": "float"})
    assert result.values["RATE"] == pytest.approx(3.14)


def test_cast_keys_bool(vault_file: Path):
    result = cast_keys(vault_file, PASSPHRASE, {"DEBUG": "bool"})
    assert result.values["DEBUG"] is True


def test_cast_keys_str(vault_file: Path):
    result = cast_keys(vault_file, PASSPHRASE, {"NAME": "str"})
    assert result.values["NAME"] == "envault"


def test_cast_keys_missing_key_recorded_as_error(vault_file: Path):
    result = cast_keys(vault_file, PASSPHRASE, {"MISSING": "int"})
    assert "MISSING" in result.errors
    assert result.ok is False


def test_cast_keys_ok_true_when_no_errors(vault_file: Path):
    result = cast_keys(vault_file, PASSPHRASE, {"PORT": "int", "NAME": "str"})
    assert result.ok is True


def test_cast_keys_as_dict_contains_fields(vault_file: Path):
    result = cast_keys(vault_file, PASSPHRASE, {"PORT": "int"})
    d = result.as_dict()
    assert "vault_path" in d
    assert "values" in d
    assert "errors" in d
    assert "ok" in d
