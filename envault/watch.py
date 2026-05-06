"""Watch a .env file for changes and automatically re-lock the vault."""

from __future__ import annotations

import time
import hashlib
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from envault.vault import Vault


class WatchError(Exception):
    """Raised when the watcher encounters an unrecoverable problem."""


@dataclass
class WatchEvent:
    env_path: Path
    vault_path: Path
    change_detected_at: float  # epoch seconds
    relocked: bool = False
    error: Optional[str] = None

    def as_dict(self) -> dict:
        return {
            "env_path": str(self.env_path),
            "vault_path": str(self.vault_path),
            "change_detected_at": self.change_detected_at,
            "relocked": self.relocked,
            "error": self.error,
        }


def _file_digest(path: Path) -> str:
    """Return SHA-256 hex digest of *path*, or empty string if missing."""
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except FileNotFoundError:
        return ""


class EnvWatcher:
    """Poll *env_path* for modifications and re-lock the vault on change."""

    def __init__(
        self,
        env_path: Path,
        passphrase: str,
        vault_path: Optional[Path] = None,
        interval: float = 2.0,
        on_event: Optional[Callable[[WatchEvent], None]] = None,
    ) -> None:
        self.env_path = Path(env_path)
        self.passphrase = passphrase
        self.vault_path = Path(vault_path) if vault_path else self.env_path.with_suffix(".vault")
        self.interval = interval
        self.on_event = on_event
        self._stop_event = threading.Event()
        self._last_digest: str = _file_digest(self.env_path)
        self._thread: Optional[threading.Thread] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start watching in a background daemon thread."""
        if self._thread and self._thread.is_alive():
            raise WatchError("Watcher is already running.")
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Signal the background thread to stop and wait for it."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=self.interval + 1)

    def is_running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _run(self) -> None:
        while not self._stop_event.wait(self.interval):
            self._check()

    def _check(self) -> None:
        digest = _file_digest(self.env_path)
        if digest == self._last_digest:
            return
        self._last_digest = digest
        event = WatchEvent(
            env_path=self.env_path,
            vault_path=self.vault_path,
            change_detected_at=time.time(),
        )
        try:
            vault = Vault(self.env_path, self.vault_path)
            vault.lock(self.passphrase)
            event.relocked = True
        except Exception as exc:  # noqa: BLE001
            event.error = str(exc)
        if self.on_event:
            self.on_event(event)
