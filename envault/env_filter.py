"""Filter vault keys by pattern, prefix, or tag membership."""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envault.vault import Vault


class FilterError(Exception):
    """Raised when filtering fails."""


@dataclass
class FilterResult:
    vault_path: Path
    matched: Dict[str, str] = field(default_factory=dict)
    total_keys: int = 0

    def as_dict(self) -> dict:
        return {
            "vault_path": str(self.vault_path),
            "matched": self.matched,
            "match_count": len(self.matched),
            "total_keys": self.total_keys,
        }


def filter_keys(
    vault_path: Path,
    passphrase: str,
    *,
    pattern: Optional[str] = None,
    prefix: Optional[str] = None,
    regex: Optional[str] = None,
) -> FilterResult:
    """Return vault entries whose keys satisfy the given filter criteria.

    At least one of *pattern* (glob), *prefix*, or *regex* must be supplied.
    If multiple are given they are ANDed together.
    """
    if pattern is None and prefix is None and regex is None:
        raise FilterError("At least one of pattern, prefix, or regex must be provided.")

    vault = Vault(vault_path)
    env_text = vault.unlock(passphrase, write=False)

    pairs: Dict[str, str] = {}
    for line in env_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        pairs[key.strip()] = value.strip()

    compiled_regex = re.compile(regex) if regex else None

    matched: Dict[str, str] = {}
    for key, value in pairs.items():
        if pattern is not None and not fnmatch.fnmatch(key, pattern):
            continue
        if prefix is not None and not key.startswith(prefix):
            continue
        if compiled_regex is not None and not compiled_regex.search(key):
            continue
        matched[key] = value

    return FilterResult(
        vault_path=vault_path,
        matched=matched,
        total_keys=len(pairs),
    )
