"""Register the format group with the main CLI and expose a helper."""
from __future__ import annotations

from pathlib import Path

import click

from envault.env_format import FormatError, format_vault


def register_format_group(cli: click.Group) -> None:
    """Attach the format sub-command group to *cli*."""
    from envault.cli_format import format_group

    cli.add_command(format_group)


def auto_format_on_lock(vault_path: Path, passphrase: str, *, silent: bool = True) -> None:
    """Optionally run formatting immediately after a vault is locked.

    Useful as a post-lock hook.  Errors are suppressed when *silent* is True
    so that a formatting hiccup never blocks the main lock workflow.
    """
    try:
        format_vault(vault_path, passphrase)
    except FormatError:
        if not silent:
            raise
    except Exception:  # pragma: no cover
        if not silent:
            raise
