"""CLI commands for the promote feature."""

from __future__ import annotations

import json
from pathlib import Path

import click

from envault.env_promote import PromoteError, promote_keys


@click.group("promote")
def promote_group() -> None:
    """Promote keys from one vault into another."""


@promote_group.command("run")
@click.argument("source", type=click.Path(exists=True, path_type=Path))
@click.argument("target", type=click.Path(exists=True, path_type=Path))
@click.option("--source-pass", prompt=True, hide_input=True, help="Source vault passphrase.")
@click.option("--target-pass", prompt=True, hide_input=True, help="Target vault passphrase.")
@click.option(
    "--key",
    "keys",
    multiple=True,
    help="Key(s) to promote. Omit to promote all keys.",
)
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Overwrite existing keys in the target vault.",
)
@click.option("--json", "as_json", is_flag=True, default=False, help="Output JSON.")
def run_cmd(
    source: Path,
    target: Path,
    source_pass: str,
    target_pass: str,
    keys: tuple,
    overwrite: bool,
    as_json: bool,
) -> None:
    """Promote keys from SOURCE vault into TARGET vault."""
    try:
        result = promote_keys(
            source_vault=source,
            source_passphrase=source_pass,
            target_vault=target,
            target_passphrase=target_pass,
            keys=list(keys) if keys else None,
            overwrite=overwrite,
        )
    except PromoteError as exc:
        raise click.ClickException(str(exc)) from exc

    if as_json:
        click.echo(json.dumps(result.as_dict(), indent=2))
        return

    click.echo(f"Promoted  : {', '.join(result.promoted) or '(none)'}")
    click.echo(f"Overwritten: {', '.join(result.overwritten) or '(none)'}")
    click.echo(f"Skipped   : {', '.join(result.skipped) or '(none)'}")
    total = len(result.promoted) + len(result.overwritten)
    click.echo(f"Done — {total} key(s) promoted into {target}.")
