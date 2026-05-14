"""Format / pretty-print .env files stored in a vault."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from envault.vault import Vault


class FormatError(Exception):
    """Raised when formatting fails."""


@dataclass
class FormatResult:
    vault_path: Path
    lines_before: int
    lines_after: int
    changes: List[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return self.lines_before != self.lines_after or bool(self.changes)

    def as_dict(self) -> dict:
        return {
            "vault_path": str(self.vault_path),
            "lines_before": self.lines_before,
            "lines_after": self.lines_after,
            "changes": self.changes,
            "changed": self.changed,
        }


def _format_lines(raw: str) -> tuple[str, list[str]]:
    """Normalise a dotenv string; return (formatted_text, list_of_change_descriptions)."""
    changes: list[str] = []
    out_lines: list[str] = []

    for lineno, line in enumerate(raw.splitlines(), 1):
        stripped = line.rstrip()

        # Remove trailing whitespace
        if stripped != line:
            changes.append(f"line {lineno}: removed trailing whitespace")

        # Blank line or comment — keep as-is (after rstrip)
        if not stripped or stripped.lstrip().startswith("#"):
            out_lines.append(stripped)
            continue

        # Ensure KEY=VALUE has no spaces around '='
        if "=" in stripped:
            key, _, value = stripped.partition("=")
            clean_key = key.strip()
            clean_value = value.strip()
            normalised = f"{clean_key}={clean_value}"
            if normalised != stripped:
                changes.append(f"line {lineno}: normalised spacing around '='")
            out_lines.append(normalised)
        else:
            out_lines.append(stripped)

    formatted = "\n".join(out_lines)
    if raw and not formatted.endswith("\n"):
        formatted += "\n"
    return formatted, changes


def format_vault(vault_path: Path, passphrase: str) -> FormatResult:
    """Decrypt vault, format its contents, then re-encrypt."""
    vault_path = Path(vault_path)
    if not vault_path.exists():
        raise FormatError(f"Vault not found: {vault_path}")

    v = Vault(vault_path.parent / vault_path.name.replace(".vault", ".env"))
    raw = v.unlock(passphrase, vault_path=vault_path)

    lines_before = len(raw.splitlines())
    formatted, changes = _format_lines(raw)
    lines_after = len(formatted.splitlines())

    # Re-lock with formatted content
    tmp_env = vault_path.parent / "_fmt_tmp.env"
    try:
        tmp_env.write_text(formatted)
        v2 = Vault(tmp_env)
        v2.lock(passphrase, vault_path=vault_path)
    finally:
        if tmp_env.exists():
            tmp_env.unlink()

    return FormatResult(
        vault_path=vault_path,
        lines_before=lines_before,
        lines_after=lines_after,
        changes=changes,
    )
