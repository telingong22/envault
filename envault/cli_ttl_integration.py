"""Helpers to wire the TTL CLI group into the main envault CLI and to
check TTL expiry as a guard before sensitive vault operations."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import click

from envault.ttl import TTLError, get_ttl


def check_vault_ttl(vault_path: Path, *, strict: bool = False) -> Optional[str]:
    """Return a warning string if the vault has an expired TTL, or None.

    Parameters
    ----------
    vault_path:
        Path to the ``.vault`` file.
    strict:
        When *True* raise :class:`click.ClickException` instead of returning
        a warning string, aborting the calling command.
    """
    try:
        record = get_ttl(vault_path)
    except TTLError:
        # No TTL configured — nothing to check.
        return None

    if record.expired:
        msg = (
            f"Vault TTL expired at {record.expires_at.isoformat()}. "
            "Secrets may be stale."
        )
        if strict:
            raise click.ClickException(msg)
        return msg

    return None


def warn_if_expired(vault_path: Path) -> None:
    """Emit a styled Click warning if the vault TTL has elapsed."""
    warning = check_vault_ttl(vault_path)
    if warning:
        click.echo(click.style(f"WARNING: {warning}", fg="yellow"), err=True)


def register_ttl_group(cli: click.Group) -> None:
    """Attach the ``ttl`` sub-group to *cli*.

    Call this from the main ``cli.py`` entry-point to make
    ``envault ttl set/status/clear`` available.

    Example
    -------
    >>> from envault.cli_ttl_integration import register_ttl_group
    >>> from envault.cli_ttl import ttl_group
    >>> register_ttl_group(cli)  # noqa: F821
    """
    from envault.cli_ttl import ttl_group  # local import avoids circular deps
    cli.add_command(ttl_group, name="ttl")
