"""Type casting for environment variable values."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from envault.vault import Vault


class CastError(Exception):
    """Raised when a value cannot be cast to the requested type."""


_BOOL_TRUE = {"1", "true", "yes", "on"}
_BOOL_FALSE = {"0", "false", "no", "off"}


def _cast_value(raw: str, type_name: str) -> Any:
    """Cast *raw* string to *type_name* (int | float | bool | str)."""
    t = type_name.lower()
    if t == "str":
        return raw
    if t == "int":
        try:
            return int(raw)
        except ValueError:
            raise CastError(f"Cannot cast {raw!r} to int")
    if t == "float":
        try:
            return float(raw)
        except ValueError:
            raise CastError(f"Cannot cast {raw!r} to float")
    if t == "bool":
        lower = raw.strip().lower()
        if lower in _BOOL_TRUE:
            return True
        if lower in _BOOL_FALSE:
            return False
        raise CastError(f"Cannot cast {raw!r} to bool")
    raise CastError(f"Unknown type {type_name!r}; expected int, float, bool, or str")


@dataclass
class CastResult:
    vault_path: Path
    values: dict[str, Any] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0

    def as_dict(self) -> dict:
        return {
            "vault_path": str(self.vault_path),
            "values": self.values,
            "errors": self.errors,
            "ok": self.ok,
        }


def cast_keys(
    vault_path: Path | str,
    passphrase: str,
    type_map: dict[str, str],
) -> CastResult:
    """Unlock *vault_path* and cast each key listed in *type_map*.

    *type_map* maps env-var key names to target type names
    (``"int"``, ``"float"``, ``"bool"``, ``"str"``).
    Missing keys are recorded as errors rather than raising.
    """
    vault_path = Path(vault_path)
    vault = Vault(vault_path)
    env_text = vault.unlock(passphrase, write=False)

    # Parse the raw env text into a dict
    pairs: dict[str, str] = {}
    for line in env_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        pairs[k.strip()] = v.strip().strip('"').strip("'")

    result = CastResult(vault_path=vault_path)
    for key, type_name in type_map.items():
        if key not in pairs:
            result.errors[key] = f"Key {key!r} not found in vault"
            continue
        try:
            result.values[key] = _cast_value(pairs[key], type_name)
        except CastError as exc:
            result.errors[key] = str(exc)

    return result
