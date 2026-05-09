"""Add, update, or remove inline comments on keys in a vault's .env file."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envault.vault import Vault


class CommentError(Exception):
    """Raised when a comment operation fails."""


@dataclass
class CommentResult:
    vault_path: Path
    updated: List[str] = field(default_factory=list)
    unchanged: List[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "vault_path": str(self.vault_path),
            "updated": self.updated,
            "unchanged": self.unchanged,
        }


def _set_comment_on_line(line: str, key: str, comment: Optional[str]) -> str:
    """Return *line* with the inline comment set or removed for *key*."""
    # Match KEY=VALUE or KEY="VALUE" with optional trailing comment
    pattern = re.compile(
        r'^(' + re.escape(key) + r'\s*=\s*(?:"[^"]*"|[^#\s]*))(\s*#.*)?$'
    )
    m = pattern.match(line)
    if not m:
        return line
    base = m.group(1).rstrip()
    if comment is None:
        return base
    return f"{base}  # {comment}"


def set_comments(
    vault_path: Path,
    passphrase: str,
    comments: Dict[str, Optional[str]],
) -> CommentResult:
    """Set or clear inline comments for *comments* keys inside *vault_path*.

    Pass ``None`` as a value to remove an existing comment for that key.
    """
    vault_path = Path(vault_path)
    if not vault_path.exists():
        raise CommentError(f"Vault not found: {vault_path}")

    v = Vault(vault_path.parent / vault_path.name.replace(".vault", ".env"))
    env_file = v.env_file

    # Unlock into a temp location so we can read/write the plaintext
    v.unlock(passphrase)
    lines = env_file.read_text().splitlines(keepends=True)

    result = CommentResult(vault_path=vault_path)
    keys_seen: set = set()

    new_lines: List[str] = []
    for line in lines:
        stripped = line.rstrip("\n")
        matched = False
        for key, comment in comments.items():
            if re.match(r'^' + re.escape(key) + r'\s*=', stripped):
                new_line = _set_comment_on_line(stripped, key, comment)
                trailing = "\n" if line.endswith("\n") else ""
                if new_line != stripped:
                    result.updated.append(key)
                else:
                    result.unchanged.append(key)
                new_lines.append(new_line + trailing)
                keys_seen.add(key)
                matched = True
                break
        if not matched:
            new_lines.append(line)

    for key in comments:
        if key not in keys_seen:
            raise CommentError(f"Key not found in env file: {key}")

    env_file.write_text("".join(new_lines))
    v.lock(passphrase)
    return result
