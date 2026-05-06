"""Inspector module: parse and display .env file contents safely."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Tuple

_ENV_LINE_RE = re.compile(
    r'^(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<value>.*)$'
)


def parse_env(path: str | Path) -> Dict[str, str]:
    """Parse a .env file and return a dict of key/value pairs.

    Blank lines and lines starting with '#' are ignored.
    Values are stripped of surrounding quotes (single or double).
    """
    result: Dict[str, str] = {}
    for key, value in _iter_pairs(Path(path).read_text(encoding="utf-8")):
        result[key] = value
    return result


def _iter_pairs(text: str) -> List[Tuple[str, str]]:
    pairs: List[Tuple[str, str]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = _ENV_LINE_RE.match(line)
        if m:
            key = m.group("key")
            value = _strip_quotes(m.group("value").strip())
            pairs.append((key, value))
    return pairs


def _strip_quotes(value: str) -> str:
    """Remove surrounding single or double quotes from a value."""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        return value[1:-1]
    return value


def mask_value(value: str, visible: int = 4) -> str:
    """Return a masked version of *value*, showing only the last *visible* chars."""
    if len(value) <= visible:
        return "*" * len(value)
    return "*" * (len(value) - visible) + value[-visible:]


def summarise(path: str | Path, mask: bool = True) -> List[Dict[str, str]]:
    """Return a list of records with 'key' and 'value' (optionally masked)."""
    pairs = parse_env(path)
    records = []
    for key, value in pairs.items():
        records.append({
            "key": key,
            "value": mask_value(value) if mask else value,
        })
    return records
