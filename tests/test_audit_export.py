"""Tests for envault.env_audit_export."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.audit import record_event
from envault.env_audit_export import export_audit, AuditExportError
from envault.cli_audit_export import audit_export_group


@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    lf = tmp_path / "audit.log"
    record_event("lock", vault=str(tmp_path / "a.vault"), log_path=lf)
    record_event("unlock", vault=str(tmp_path / "a.vault"), note="test", log_path=lf)
    return lf


# --- export_audit unit tests ---

def test_export_json_returns_string(log_file: Path) -> None:
    result = export_audit(fmt="json", log_path=log_file)
    assert isinstance(result, str)


def test_export_json_is_valid_json(log_file: Path) -> None:
    result = export_audit(fmt="json", log_path=log_file)
    data = json.loads(result)
    assert isinstance(data, list)
    assert len(data) == 2


def test_export_json_contains_event_field(log_file: Path) -> None:
    data = json.loads(export_audit(fmt="json", log_path=log_file))
    assert data[0]["event"] == "lock"


def test_export_csv_returns_string(log_file: Path) -> None:
    result = export_audit(fmt="csv", log_path=log_file)
    assert isinstance(result, str)


def test_export_csv_has_header(log_file: Path) -> None:
    result = export_audit(fmt="csv", log_path=log_file)
    assert "timestamp" in result
    assert "event" in result


def test_export_csv_contains_event_names(log_file: Path) -> None:
    result = export_audit(fmt="csv", log_path=log_file)
    assert "lock" in result
    assert "unlock" in result


def test_export_text_returns_string(log_file: Path) -> None:
    result = export_audit(fmt="text", log_path=log_file)
    assert isinstance(result, str)


def test_export_text_contains_event(log_file: Path) -> None:
    result = export_audit(fmt="text", log_path=log_file)
    assert "lock" in result


def test_export_unsupported_format_raises(log_file: Path) -> None:
    with pytest.raises(AuditExportError):
        export_audit(fmt="xml", log_path=log_file)


def test_export_writes_output_file(log_file: Path, tmp_path: Path) -> None:
    out = tmp_path / "export.json"
    export_audit(fmt="json", log_path=log_file, output_path=out)
    assert out.exists()
    assert len(json.loads(out.read_text())) == 2


# --- CLI tests ---

@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_run_command_exits_ok(runner: CliRunner, log_file: Path) -> None:
    result = runner.invoke(audit_export_group, ["run", "--log", str(log_file)])
    assert result.exit_code == 0


def test_run_command_json_output(runner: CliRunner, log_file: Path) -> None:
    result = runner.invoke(audit_export_group, ["run", "--log", str(log_file), "--format", "json"])
    data = json.loads(result.output)
    assert len(data) == 2


def test_run_command_csv_output(runner: CliRunner, log_file: Path) -> None:
    result = runner.invoke(audit_export_group, ["run", "--log", str(log_file), "--format", "csv"])
    assert "event" in result.output


def test_run_command_writes_file(runner: CliRunner, log_file: Path, tmp_path: Path) -> None:
    out = tmp_path / "out.json"
    result = runner.invoke(audit_export_group, ["run", "--log", str(log_file), "--output", str(out)])
    assert result.exit_code == 0
    assert out.exists()
    assert "exported" in result.output
