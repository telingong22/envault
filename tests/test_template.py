"""Tests for envault.template — template rendering with vault secrets."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from envault.template import render_string, render_file, TemplateError
from envault.vault import Vault


PASSPHRASE = "test-passphrase"
SECRETS = {"DB_HOST": "localhost", "DB_PORT": "5432", "API_KEY": "abc123"}


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    env.write_text("\n".join(f"{k}={v}" for k, v in SECRETS.items()))
    v = Vault(tmp_path / ".env.vault")
    v.lock(env, PASSPHRASE)
    return tmp_path / ".env.vault"


@pytest.fixture()
def template_file(tmp_path: Path) -> Path:
    tpl = tmp_path / "config.tpl"
    tpl.write_text("host={{ DB_HOST }}\nport={{ DB_PORT }}\nkey={{API_KEY}}\n")
    return tpl


# --- render_string -----------------------------------------------------------

def test_render_string_substitutes_all_keys():
    result = render_string("Hello {{ NAME }}!", {"NAME": "world"})
    assert result == "Hello world!"


def test_render_string_whitespace_tolerant():
    result = render_string("{{KEY}} and {{ KEY }}", {"KEY": "val"})
    assert result == "val and val"


def test_render_string_multiple_keys():
    tpl = "{{ A }}-{{ B }}-{{ C }}"
    result = render_string(tpl, {"A": "1", "B": "2", "C": "3"})
    assert result == "1-2-3"


def test_render_string_strict_raises_on_missing():
    with pytest.raises(TemplateError, match="undefined keys"):
        render_string("{{ MISSING }}", {}, strict=True)


def test_render_string_non_strict_leaves_placeholder():
    result = render_string("{{ MISSING }}", {}, strict=False)
    assert "{{ MISSING }}" in result


def test_render_string_strict_error_lists_all_missing():
    with pytest.raises(TemplateError) as exc_info:
        render_string("{{ A }} {{ B }}", {}, strict=True)
    assert "A" in str(exc_info.value)
    assert "B" in str(exc_info.value)


# --- render_file -------------------------------------------------------------

def test_render_file_returns_string(vault_file: Path, template_file: Path):
    result = render_file(template_file, vault_file, PASSPHRASE)
    assert isinstance(result, str)


def test_render_file_substitutes_secrets(vault_file: Path, template_file: Path):
    result = render_file(template_file, vault_file, PASSPHRASE)
    assert "localhost" in result
    assert "5432" in result
    assert "abc123" in result


def test_render_file_writes_output(vault_file: Path, template_file: Path, tmp_path: Path):
    out = tmp_path / "config.rendered"
    render_file(template_file, vault_file, PASSPHRASE, output_path=out)
    assert out.exists()
    assert "localhost" in out.read_text()


def test_render_file_missing_template_raises(vault_file: Path, tmp_path: Path):
    with pytest.raises(TemplateError, match="not found"):
        render_file(tmp_path / "no_such.tpl", vault_file, PASSPHRASE)


def test_render_file_no_output_path_does_not_create_file(
    vault_file: Path, template_file: Path, tmp_path: Path
):
    render_file(template_file, vault_file, PASSPHRASE)
    # Only the template and vault should exist; no extra rendered file
    extra = [p for p in tmp_path.iterdir() if p.suffix == ".rendered"]
    assert extra == []
