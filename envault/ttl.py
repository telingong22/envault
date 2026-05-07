"""TTL (time-to-live) support for vault secrets — mark a vault with an
expiry timestamp and check whether it has expired."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


class TTLError(Exception):
    """Raised when a TTL operation fails."""


@dataclass
class TTLRecord:
    vault_path: Path
    expires_at: datetime
    note: str

    @property
    def expired(self) -> bool:
        return datetime.now(timezone.utc) >= self.expires_at

    @property
    def seconds_remaining(self) -> float:
        delta = self.expires_at - datetime.now(timezone.utc)
        return max(delta.total_seconds(), 0.0)

    def as_dict(self) -> dict:
        return {
            "vault_path": str(self.vault_path),
            "expires_at": self.expires_at.isoformat(),
            "note": self.note,
            "expired": self.expired,
            "seconds_remaining": self.seconds_remaining,
        }


def _ttl_path(vault_path: Path) -> Path:
    return vault_path.with_suffix(".ttl.json")


def set_ttl(vault_path: Path, seconds: float, note: str = "") -> TTLRecord:
    """Attach a TTL to *vault_path*. Raises TTLError if seconds <= 0."""
    vault_path = Path(vault_path)
    if not vault_path.exists():
        raise TTLError(f"Vault not found: {vault_path}")
    if seconds <= 0:
        raise TTLError("TTL must be a positive number of seconds.")
    expires_at = datetime.now(timezone.utc).replace(microsecond=0)
    from datetime import timedelta
    expires_at = expires_at + timedelta(seconds=seconds)
    record = TTLRecord(vault_path=vault_path, expires_at=expires_at, note=note)
    _ttl_path(vault_path).write_text(
        json.dumps(record.as_dict(), indent=2), encoding="utf-8"
    )
    return record


def get_ttl(vault_path: Path) -> TTLRecord:
    """Return the TTLRecord for *vault_path*. Raises TTLError if none set."""
    vault_path = Path(vault_path)
    ttl_file = _ttl_path(vault_path)
    if not ttl_file.exists():
        raise TTLError(f"No TTL set for vault: {vault_path}")
    data = json.loads(ttl_file.read_text(encoding="utf-8"))
    return TTLRecord(
        vault_path=vault_path,
        expires_at=datetime.fromisoformat(data["expires_at"]),
        note=data.get("note", ""),
    )


def clear_ttl(vault_path: Path) -> bool:
    """Remove the TTL file for *vault_path*. Returns True if removed."""
    ttl_file = _ttl_path(Path(vault_path))
    if ttl_file.exists():
        ttl_file.unlink()
        return True
    return False
