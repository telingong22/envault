"""Tests for envault.lint."""
import pytest
from pathlib import Path

from envault.lint import lint_env, LintResult, LintIssue


@pytest.fixture
def env_file(tmp_path):
    def _make(content: str) -> Path:
        p = tmp_path / ".env"
        p.write_text(content)
        return p
    return _make


def test_lint_returns_lint_result(env_file):
    p = env_file("KEY=value\n")
    assert isinstance(lint_env(p), LintResult)


def test_clean_file_has_no_issues(env_file):
    p = env_file("KEY=value\nOTHER=123\n")
    result = lint_env(p)
    assert result.issues == []
    assert result.ok is True


def test_missing_file_gives_error(tmp_path):
    result = lint_env(tmp_path / "missing.env")
    assert result.error_count == 1
    assert result.issues[0].code == "FILE_NOT_FOUND"
    assert result.ok is False


def test_duplicate_key_is_error(env_file):
    p = env_file("KEY=a\nKEY=b\n")
    result = lint_env(p)
    errors = [i for i in result.issues if i.code == "DUPLICATE_KEY"]
    assert len(errors) == 1
    assert result.ok is False


def test_empty_value_is_warning(env_file):
    p = env_file("KEY=\n")
    result = lint_env(p)
    warnings = [i for i in result.issues if i.code == "EMPTY_VALUE"]
    assert len(warnings) == 1
    assert result.ok is True  # only warning, not error


def test_invalid_key_chars_warning(env_file):
    p = env_file("MY-KEY=value\n")
    result = lint_env(p)
    warnings = [i for i in result.issues if i.code == "INVALID_KEY_CHARS"]
    assert len(warnings) == 1


def test_no_equals_is_warning(env_file):
    p = env_file("BADLINE\n")
    result = lint_env(p)
    warnings = [i for i in result.issues if i.code == "NO_EQUALS"]
    assert len(warnings) == 1


def test_comments_and_blanks_ignored(env_file):
    p = env_file("# comment\n\nKEY=value\n")
    result = lint_env(p)
    assert result.issues == []


def test_summary_string(env_file):
    p = env_file("KEY=a\nKEY=b\n")
    result = lint_env(p)
    s = result.summary()
    assert "error" in s
    assert str(p) in s


def test_issue_as_dict(env_file):
    p = env_file("KEY=\n")
    result = lint_env(p)
    d = result.issues[0].as_dict()
    assert set(d.keys()) == {"level", "code", "message", "line"}


def test_error_and_warning_counts(env_file):
    p = env_file("KEY=a\nKEY=b\nEMPTY=\n")
    result = lint_env(p)
    assert result.error_count == 1
    assert result.warning_count == 1
