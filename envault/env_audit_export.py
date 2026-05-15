"""Export audit log to various formats (JSON, CSV, text)."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import List, Optional

from envault.audit import read_log, _default_log_path


class AuditExportError(Exception):
    """Raised when audit export fails."""


def _to_json(entries: List[dict]) -> str:
    return json.dumps(entries, indent=2)


def _to_csv(entries: List[dict]) -> str:
    if not entries:
        return ""
    buf = io.StringIO()
    fieldnames = ["timestamp", "event", "vault", "note"]
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for entry in entries:
        writer.writerow({
            "timestamp": entry.get("timestamp", ""),
            "event": entry.get("event", ""),
            "vault": entry.get("vault", ""),
            "note": entry.get("note", ""),
        })
    return buf.getvalue()


def _to_text(entries: List[dict]) -> str:
    lines = []
    for e in entries:
        ts = e.get("timestamp", "unknown")
        event = e.get("event", "unknown")
        vault = e.get("vault", "")
        note = e.get("note", "")
        parts = [f"[{ts}] {event}"]
        if vault:
            parts.append(f"vault={vault}")
        if note:
            parts.append(f"note={note}")
        lines.append("  ".join(parts))
    return "\n".join(lines)


def export_audit(
    fmt: str = "json",
    log_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
) -> str:
    """Read the audit log and return it serialised in *fmt* (json|csv|text).

    If *output_path* is given the result is also written to that file.
    Returns the serialised string.
    """
    fmt = fmt.lower()
    if fmt not in ("json", "csv", "text"):
        raise AuditExportError(f"Unsupported format: {fmt!r}. Choose json, csv, or text.")

    resolved = Path(log_path) if log_path else _default_log_path()
    entries = read_log(resolved)

    if fmt == "json":
        result = _to_json(entries)
    elif fmt == "csv":
        result = _to_csv(entries)
    else:
        result = _to_text(entries)

    if output_path is not None:
        Path(output_path).write_text(result, encoding="utf-8")

    return result
