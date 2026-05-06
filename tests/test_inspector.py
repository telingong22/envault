"""Tests for envault.inspector."""

import pytest
from pathlib import Path

from envault.inspector import parse_env, mask_value, summarise, _strip_quotes


@pytest.fixture
def env_file(tmp_path: Path) -> Path:
    content = (
        "# database settings\n"
        "DB_HOST=localhost\n"
        "DB_PORT=5432\n"
        "DB_PASSWORD=\"super_secret\"\n"
        "API_KEY='abc123xyz'\n"
        "EMPTY_VAR=\n"
        "\n"
        "# trailing comment\n"
    )
    p = tmp_path / ".env"
    p.write_text(content, encoding="utf-8")
    return p


def test_parse_env_returns_dict(env_file: Path):
    result = parse_env(env_file)
    assert isinstance(result, dict)


def test_parse_env_correct_keys(env_file: Path):
    result = parse_env(env_file)
    assert set(result.keys()) == {"DB_HOST", "DB_PORT", "DB_PASSWORD", "API_KEY", "EMPTY_VAR"}


def test_parse_env_values(env_file: Path):
    result = parse_env(env_file)
    assert result["DB_HOST"] == "localhost"
    assert result["DB_PORT"] == "5432"


def test_parse_env_strips_double_quotes(env_file: Path):
    result = parse_env(env_file)
    assert result["DB_PASSWORD"] == "super_secret"


def test_parse_env_strips_single_quotes(env_file: Path):
    result = parse_env(env_file)
    assert result["API_KEY"] == "abc123xyz"


def test_parse_env_empty_value(env_file: Path):
    result = parse_env(env_file)
    assert result["EMPTY_VAR"] == ""


def test_strip_quotes_no_quotes():
    assert _strip_quotes("hello") == "hello"


def test_mask_value_long():
    masked = mask_value("supersecret", visible=4)
    assert masked.endswith("cret")
    assert masked.startswith("*")
    assert len(masked) == len("supersecret")


def test_mask_value_short():
    masked = mask_value("ab", visible=4)
    assert masked == "**"


def test_summarise_masks_by_default(env_file: Path):
    records = summarise(env_file)
    for rec in records:
        assert "key" in rec and "value" in rec
    passwords = [r for r in records if r["key"] == "DB_PASSWORD"]
    assert passwords[0]["value"] != "super_secret"


def test_summarise_no_mask(env_file: Path):
    records = summarise(env_file, mask=False)
    passwords = [r for r in records if r["key"] == "DB_PASSWORD"]
    assert passwords[0]["value"] == "super_secret"
