"""Integration helpers — register the diff-apply group with the main CLI."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import click


def register_diff_apply_group(cli: "click.Group") -> None:
    """Attach the ``diff-apply`` command group to *cli*.

    Call this from the main :mod:`envault.cli` module during app initialisation::

        from envault.cli_diff_apply_integration import register_diff_apply_group
        register_diff_apply_group(cli)
    """
    from envault.cli_diff_apply import diff_apply_group  # local import avoids circular deps

    cli.add_command(diff_apply_group)


def diff_apply_summary(result: object) -> str:
    """Return a human-readable one-liner summarising an :class:`~envault.env_diff_apply.ApplyResult`.

    >>> from envault.env_diff_apply import ApplyResult
    >>> r = ApplyResult(vault_path="v", added=["A"], updated=["B"], removed=[])
    >>> diff_apply_summary(r)
    '1 added, 1 updated, 0 removed'
    """
    added = len(getattr(result, "added", []))
    updated = len(getattr(result, "updated", []))
    removed = len(getattr(result, "removed", []))
    return f"{added} added, {updated} updated, {removed} removed"
