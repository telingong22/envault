"""CLI commands for applying a diff to a vault."""
from __future__ import annotations

import json
from pathlib import Path

import click

from envault.env_diff_apply import apply_diff, ApplyError


@click.group("diff-apply")
def diff_apply_group() -> None:
    """Apply key/value changes to a vault from a target env file or inline pairs."""


@diff_apply_group.command("run")
@click.argument("vault", type=click.Path(exists=True, path_type=Path))
@click.option("--passphrase", "-p", required=True, envvar="ENVAULT_PASSPHRASE", help="Master passphrase.")
@click.option("--target", "-t", "target_file", type=click.Path(exists=True, path_type=Path), default=None,
              help="Target .env file to apply.")
@click.option("--set", "-s", "pairs", multiple=True, metavar="KEY=VALUE",
              help="Inline KEY=VALUE pairs to apply.")
@click.option("--remove-missing", is_flag=True, default=False,
              help="Remove keys absent from target.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Preview changes without writing.")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def run_cmd(
    vault: Path,
    passphrase: str,
    target_file: Path | None,
    pairs: tuple[str, ...],
    remove_missing: bool,
    dry_run: bool,
    as_json: bool,
) -> None:
    """Apply a set of changes to VAULT."""
    target: dict[str, str] = {}

    if target_file:
        for line in target_file.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            target[k.strip()] = v.strip()

    for pair in pairs:
        if "=" not in pair:
            raise click.BadParameter(f"Expected KEY=VALUE, got: {pair!r}", param_hint="--set")
        k, _, v = pair.partition("=")
        target[k.strip()] = v.strip()

    try:
        result = apply_diff(vault, passphrase, target, remove_missing=remove_missing, dry_run=dry_run)
    except ApplyError as exc:
        raise click.ClickException(str(exc)) from exc

    if as_json:
        click.echo(json.dumps(result.as_dict(), indent=2))
        return

    prefix = "[dry-run] " if dry_run else ""
    if not result.has_changes():
        click.echo(f"{prefix}No changes to apply.")
        return

    if result.added:
        click.echo(f"{prefix}Added:   {', '.join(result.added)}")
    if result.updated:
        click.echo(f"{prefix}Updated: {', '.join(result.updated)}")
    if result.removed:
        click.echo(f"{prefix}Removed: {', '.join(result.removed)}")
