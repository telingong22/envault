"""Redact sensitive values in a vault by replacing them with placeholder text."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from envault.vault import Vault

_DEFAULT_PLACEHOLDER = "***REDACTED***"


class RedactError(Exception):
    """Raised when redaction fails."""


@dataclass
class RedactResult:
    vault_path: str
    redacted: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    def has_changes(self) -> bool:
        return bool(self.redacted)

    def as_dict(self) -> dict:
        return {
            "vault_path": self.vault_path,
            "redacted": self.redacted,
            "skipped": self.skipped,
            "has_changes": self.has_changes(),
        }


def _redact_lines(
    lines: List[str],
    keys: List[str],
    placeholder: str,
) -> tuple[List[str], List[str], List[str]]:
    """Return (new_lines, redacted_keys, skipped_keys)."""
    key_set = set(keys)
    redacted: List[str] = []
    skipped: List[str] = []
    new_lines: List[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            new_lines.append(line)
            continue
        if "=" not in stripped:
            new_lines.append(line)
            continue
        k, _ = stripped.split("=", 1)
        k = k.strip()
        if k in key_set:
            new_lines.append(f"{k}={placeholder}\n")
            redacted.append(k)
            key_set.discard(k)
        else:
            new_lines.append(line)

    skipped = list(key_set)
    return new_lines, redacted, skipped


def redact_keys(
    vault_path: str | Path,
    passphrase: str,
    keys: List[str],
    placeholder: str = _DEFAULT_PLACEHOLDER,
) -> RedactResult:
    """Redact *keys* inside *vault_path*, replacing their values with *placeholder*."""
    vault_path = Path(vault_path)
    if not vault_path.exists():
        raise RedactError(f"Vault not found: {vault_path}")
    if not keys:
        raise RedactError("No keys specified for redaction.")

    v = Vault(vault_path)
    env_path = vault_path.with_suffix(".env")
    v.unlock(passphrase, output=env_path)

    try:
        raw_lines = env_path.read_text().splitlines(keepends=True)
        new_lines, redacted, skipped = _redact_lines(raw_lines, keys, placeholder)
        env_path.write_text("".join(new_lines))
        v.lock(passphrase, env_file=env_path)
    finally:
        if env_path.exists():
            env_path.unlink()

    return RedactResult(
        vault_path=str(vault_path),
        redacted=redacted,
        skipped=skipped,
    )
