"""Search across vault keys and values."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envault.vault import Vault
from envault.inspector import parse_env


class SearchError(Exception):
    """Raised when a search operation fails."""


@dataclass
class SearchMatch:
    key: str
    value: str
    match_in: str  # 'key', 'value', or 'both'


@dataclass
class SearchResult:
    vault_path: Path
    pattern: str
    matches: List[SearchMatch] = field(default_factory=list)

    @property
    def found(self) -> bool:
        return len(self.matches) > 0

    def summary(self) -> str:
        if not self.found:
            return f"No matches for '{self.pattern}' in {self.vault_path.name}"
        lines = [f"Found {len(self.matches)} match(es) for '{self.pattern}' in {self.vault_path.name}:"]
        for m in self.matches:
            lines.append(f"  [{m.match_in}] {m.key}")
        return "\n".join(lines)


def search_vault(
    vault_path: Path,
    passphrase: str,
    pattern: str,
    *,
    search_keys: bool = True,
    search_values: bool = False,
    case_sensitive: bool = False,
) -> SearchResult:
    """Search a locked vault for keys/values matching *pattern*.

    Parameters
    ----------
    vault_path:     Path to the ``.vault`` file.
    passphrase:     Master passphrase used to decrypt the vault.
    pattern:        Regular-expression pattern to search for.
    search_keys:    Include key names in the search (default True).
    search_values:  Include plaintext values in the search (default False).
    case_sensitive: Use case-sensitive matching (default False).
    """
    vault_path = Path(vault_path)
    if not vault_path.exists():
        raise SearchError(f"Vault file not found: {vault_path}")

    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        compiled = re.compile(pattern, flags)
    except re.error as exc:
        raise SearchError(f"Invalid pattern '{pattern}': {exc}") from exc

    # Decrypt to a temporary in-memory string
    vault = Vault(vault_path.parent / ".env", vault_path=vault_path)
    try:
        plaintext = vault.unlock(passphrase, write=False)
    except Exception as exc:
        raise SearchError(f"Could not decrypt vault: {exc}") from exc

    env: Dict[str, str] = parse_env(plaintext)
    result = SearchResult(vault_path=vault_path, pattern=pattern)

    for key, value in env.items():
        in_key = search_keys and bool(compiled.search(key))
        in_value = search_values and bool(compiled.search(value))
        if in_key or in_value:
            match_in = "both" if (in_key and in_value) else ("key" if in_key else "value")
            result.matches.append(SearchMatch(key=key, value=value, match_in=match_in))

    return result
