"""Integration helpers to wire the freeze group into the main CLI."""
from __future__ import annotations

from pathlib import Path

import click

from envault.cli_freeze import freeze_group
from envault.env_freeze import FreezeError, diff_freeze


def register_freeze_group(cli: click.Group) -> None:
    """Attach the ``freeze`` sub-group to *cli*."""
    cli.add_command(freeze_group)


def warn_if_drift(vault_path: Path, passphrase: str) -> bool:
    """Return *True* and print a warning when drift is detected.

    Silently returns *False* when no freeze file exists or there is no drift.
    """
    try:
        result = diff_freeze(vault_path, passphrase)
    except FreezeError:
        # No freeze file present — nothing to compare against.
        return False

    has_drift = any([result["added"], result["removed"], result["changed"]])
    if has_drift:
        total = (
            len(result["added"]) + len(result["removed"]) + len(result["changed"])
        )
        click.echo(
            click.style(
                f"⚠  Drift detected: {total} key(s) differ from the frozen state.",
                fg="yellow",
            ),
            err=True,
        )
    return has_drift
