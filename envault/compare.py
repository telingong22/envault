"""Compare two vault files and report key-level differences."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envault.vault import Vault


class CompareError(Exception):
    """Raised when a vault comparison fails."""


@dataclass
class CompareResult:
    only_in_a: List[str] = field(default_factory=list)
    only_in_b: List[str] = field(default_factory=list)
    changed: List[str] = field(default_factory=list)
    identical: List[str] = field(default_factory=list)

    @property
    def has_differences(self) -> bool:
        return bool(self.only_in_a or self.only_in_b or self.changed)

    def as_dict(self) -> Dict:
        return {
            "only_in_a": sorted(self.only_in_a),
            "only_in_b": sorted(self.only_in_b),
            "changed": sorted(self.changed),
            "identical": sorted(self.identical),
            "has_differences": self.has_differences,
        }

    def summary(self) -> str:
        lines = []
        for k in sorted(self.only_in_a):
            lines.append(f"  only in A : {k}")
        for k in sorted(self.only_in_b):
            lines.append(f"  only in B : {k}")
        for k in sorted(self.changed):
            lines.append(f"  changed   : {k}")
        for k in sorted(self.identical):
            lines.append(f"  identical : {k}")
        if not lines:
            return "Vaults are identical."
        return "\n".join(lines)


def _unlock_vault(vault_path: Path, passphrase: str) -> Dict[str, str]:
    """Unlock a vault and return its key/value pairs."""
    import tempfile, os
    from envault.inspector import parse_env

    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        v = Vault(tmp_path, vault_path)
        v.unlock(passphrase)
        return parse_env(tmp_path)
    except Exception as exc:
        raise CompareError(
            f"Failed to unlock vault '{vault_path}': {exc}"
        ) from exc
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def compare_vaults(
    vault_a: Path,
    vault_b: Path,
    passphrase_a: str,
    passphrase_b: Optional[str] = None,
) -> CompareResult:
    """Compare the decrypted contents of two vault files."""
    passphrase_b = passphrase_b or passphrase_a

    if not vault_a.exists():
        raise CompareError(f"Vault not found: {vault_a}")
    if not vault_b.exists():
        raise CompareError(f"Vault not found: {vault_b}")

    env_a = _unlock_vault(vault_a, passphrase_a)
    env_b = _unlock_vault(vault_b, passphrase_b)

    keys_a, keys_b = set(env_a), set(env_b)
    result = CompareResult(
        only_in_a=list(keys_a - keys_b),
        only_in_b=list(keys_b - keys_a),
    )
    for key in keys_a & keys_b:
        if env_a[key] == env_b[key]:
            result.identical.append(key)
        else:
            result.changed.append(key)
    return result
