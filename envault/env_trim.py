"""env_trim.py – Strip leading/trailing whitespace from env values inside a vault."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from envault.vault import Vault


class TrimError(Exception):
    """Raised when trimming fails."""


@dataclass
class TrimResult:
    vault_path: str
    trimmed: List[str] = field(default_factory=list)
    unchanged: List[str] = field(default_factory=list)

    def has_changes(self) -> bool:
        return bool(self.trimmed)

    def as_dict(self) -> dict:
        return {
            "vault_path": self.vault_path,
            "trimmed": self.trimmed,
            "unchanged": self.unchanged,
            "has_changes": self.has_changes(),
        }


def _trim_lines(lines: List[str]) -> tuple[List[str], List[str], List[str]]:
    """Return (new_lines, trimmed_keys, unchanged_keys)."""
    new_lines: List[str] = []
    trimmed: List[str] = []
    unchanged: List[str] = []

    for line in lines:
        stripped = line.rstrip("\n")
        if not stripped or stripped.lstrip().startswith("#") or "=" not in stripped:
            new_lines.append(line)
            continue

        key, _, value = stripped.partition("=")
        key = key.strip()
        trimmed_value = value.strip()

        if trimmed_value != value:
            new_lines.append(f"{key}={trimmed_value}\n")
            trimmed.append(key)
        else:
            new_lines.append(line)
            unchanged.append(key)

    return new_lines, trimmed, unchanged


def trim_values(
    vault_path: str | Path,
    passphrase: str,
) -> TrimResult:
    """Decrypt *vault_path*, trim all env values, re-encrypt and return a TrimResult."""
    vault_path = Path(vault_path)
    if not vault_path.exists():
        raise TrimError(f"Vault not found: {vault_path}")

    vault = Vault(vault_path)

    import tempfile, os

    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        vault.unlock(passphrase, dest=tmp_path)
        raw_lines = tmp_path.read_text().splitlines(keepends=True)
        new_lines, trimmed, unchanged = _trim_lines(raw_lines)
        tmp_path.write_text("".join(new_lines))
        vault2 = Vault(vault_path)
        vault2.lock(passphrase, src=tmp_path)
    finally:
        if tmp_path.exists():
            os.unlink(tmp_path)

    return TrimResult(
        vault_path=str(vault_path),
        trimmed=trimmed,
        unchanged=unchanged,
    )
