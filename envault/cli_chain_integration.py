"""Integration helpers – attach the chain group to the main CLI."""
from __future__ import annotations

import click

from envault.cli_chain import chain_group


def register_chain_group(cli: click.Group) -> None:
    """Attach the *chain* sub-group to *cli*.

    Call this from the main ``cli.py`` entry-point::

        from envault.cli_chain_integration import register_chain_group
        register_chain_group(cli)
    """
    cli.add_command(chain_group)


def chain_lookup_summary(result) -> str:
    """Return a one-line human-readable summary of a :class:`ChainResult`."""
    if result.found:
        return (
            f"'{result.key}' resolved to '{result.value}' "
            f"(from {result.found_in.name})"
        )
    checked = ", ".join(p.name for p in result.checked)
    return f"'{result.key}' not found in chain [{checked}]"
