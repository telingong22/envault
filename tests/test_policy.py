"""Tests for envault.policy."""
import pytest
from pathlib import Path

from envault.policy import check_policy, PolicyError, PolicyResult, PolicyViolation


@pytest.fixture
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("DB_HOST=localhost\nDB_PASS=secret123\nAPI_KEY=\nSECRET=hi\n")
    return p


def test_check_policy_returns_policy_result(env_file):
    result = check_policy(env_file)
    assert isinstance(result, PolicyResult)


def test_clean_file_passes_by_default(env_file):
    result = check_policy(env_file)
    assert result.ok


def test_missing_file_raises(tmp_path):
    with pytest.raises(PolicyError):
        check_policy(tmp_path / "missing.env")


def test_no_empty_values_detects_empty(env_file):
    result = check_policy(env_file, no_empty_values=True)
    assert not result.ok
    keys = [v.key for v in result.violations]
    assert "API_KEY" in keys


def test_no_empty_values_passes_when_all_set(tmp_path):
    p = tmp_path / ".env"
    p.write_text("A=1\nB=2\n")
    result = check_policy(p, no_empty_values=True)
    assert result.ok


def test_min_length_detects_short_values(env_file):
    result = check_policy(env_file, min_length=5)
    assert not result.ok
    keys = [v.key for v in result.violations]
    assert "SECRET" in keys  # value 'hi' is 2 chars


def test_min_length_rule_name(env_file):
    result = check_policy(env_file, min_length=5)
    rules = [v.rule for v in result.violations]
    assert "min_length" in rules


def test_key_pattern_detects_non_matching(env_file):
    result = check_policy(env_file, key_pattern=r"[A-Z][A-Z0-9_]+")
    assert result.ok  # all keys match UPPER_SNAKE


def test_key_pattern_flags_lowercase(tmp_path):
    p = tmp_path / ".env"
    p.write_text("myKey=value\n")
    result = check_policy(p, key_pattern=r"[A-Z][A-Z0-9_]+")
    assert not result.ok
    assert result.violations[0].rule == "key_pattern"


def test_required_keys_missing(env_file):
    result = check_policy(env_file, required_keys=["DB_HOST", "MISSING_KEY"])
    assert not result.ok
    keys = [v.key for v in result.violations]
    assert "MISSING_KEY" in keys
    assert "DB_HOST" not in keys


def test_required_keys_all_present(env_file):
    result = check_policy(env_file, required_keys=["DB_HOST", "DB_PASS"])
    assert result.ok


def test_summary_ok(tmp_path):
    p = tmp_path / ".env"
    p.write_text("A=hello\n")
    result = check_policy(p)
    assert "passed" in result.summary()


def test_summary_violations(env_file):
    result = check_policy(env_file, no_empty_values=True)
    summary = result.summary()
    assert "violation" in summary
    assert "API_KEY" in summary


def test_violation_as_dict(env_file):
    result = check_policy(env_file, no_empty_values=True)
    d = result.violations[0].as_dict()
    assert "key" in d and "rule" in d and "message" in d
