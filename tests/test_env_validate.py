"""Tests for envault.env_validate."""
from __future__ import annotations

import pytest
from pathlib import Path

from envault.vault import Vault
from envault.env_validate import (
    ValidateError,
    ValidationResult,
    ValidationViolation,
    validate_vault,
)

PASS = "s3cret"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    env.write_text("API_KEY=abc123\nENV=production\nPORT=8080\n")
    v = Vault(env)
    v.lock(PASS)
    return tmp_path / ".env.vault"


def test_validate_returns_validation_result(vault_file):
    result = validate_vault(vault_file, PASS, {})
    assert isinstance(result, ValidationResult)


def test_validate_vault_path_in_result(vault_file):
    result = validate_vault(vault_file, PASS, {})
    assert str(vault_file) in result.vault_path


def test_validate_no_rules_passes(vault_file):
    result = validate_vault(vault_file, PASS, {})
    assert result.ok is True
    assert result.violation_count == 0


def test_validate_regex_match_passes(vault_file):
    result = validate_vault(vault_file, PASS, {"API_KEY": {"regex": r"[a-z0-9]+"}})
    assert result.ok is True


def test_validate_regex_mismatch_fails(vault_file):
    result = validate_vault(vault_file, PASS, {"API_KEY": {"regex": r"\d+"}})
    assert result.ok is False
    assert result.violation_count == 1
    assert result.violations[0].key == "API_KEY"
    assert result.violations[0].rule == "regex"


def test_validate_choices_pass(vault_file):
    result = validate_vault(vault_file, PASS, {"ENV": {"choices": ["production", "staging"]}})
    assert result.ok is True


def test_validate_choices_fail(vault_file):
    result = validate_vault(vault_file, PASS, {"ENV": {"choices": ["dev", "staging"]}})
    assert result.ok is False
    assert result.violations[0].rule == "choices"


def test_validate_min_length_pass(vault_file):
    result = validate_vault(vault_file, PASS, {"API_KEY": {"min_length": 3}})
    assert result.ok is True


def test_validate_min_length_fail(vault_file):
    result = validate_vault(vault_file, PASS, {"API_KEY": {"min_length": 100}})
    assert result.ok is False
    assert result.violations[0].rule == "min_length"


def test_validate_max_length_fail(vault_file):
    result = validate_vault(vault_file, PASS, {"API_KEY": {"max_length": 2}})
    assert result.ok is False
    assert result.violations[0].rule == "max_length"


def test_validate_as_dict_keys(vault_file):
    result = validate_vault(vault_file, PASS, {})
    d = result.as_dict()
    assert "vault_path" in d
    assert "ok" in d
    assert "violation_count" in d
    assert "violations" in d


def test_validate_missing_vault_raises(tmp_path):
    with pytest.raises(ValidateError):
        validate_vault(tmp_path / "ghost.vault", PASS, {})


def test_violation_as_dict():
    v = ValidationViolation("KEY", "regex", "bad")
    d = v.as_dict()
    assert d["key"] == "KEY"
    assert d["rule"] == "regex"
    assert d["message"] == "bad"
