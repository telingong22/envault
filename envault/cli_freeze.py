"""CLI commands for vault freeze / drift-detection."""
from __future__ import annotations

import json
from pathlib import Path

import click

from envault.env_freeze import FreezeError, diff_freeze, freeze_vault, load_freeze


@click.group("freeze", help="Freeze vault state and detect drift.")
def freeze_group() -> None:  # pragma: no cover
    pass


@freeze_group.command("save", help="Snapshot the current vault state to a freeze file.")
@click.argument("vault", type=click.Path())
@click.option("--passphrase", "-p", prompt=True, hide_input=True)
def save_cmd(vault: str, passphrase: str) -> None:
    try:
        result = freeze_vault(Path(vault), passphrase)
        click.echo(f"Frozen {len(result.keys)} keys → {result.freeze_path}")
        click.echo(f"Timestamp: {result.timestamp}")
    except FreezeError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@freeze_group.command("show", help="Display the contents of a freeze file.")
@click.argument("vault", type=click.Path())
@click.option("--json", "as_json", is_flag=True, default=False)
def show_cmd(vault: str, as_json: bool) -> None:
    try:
        data = load_freeze(Path(vault))
    except FreezeError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

    if as_json:
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(f"Frozen at : {data['timestamp']}")
        click.echo(f"Keys ({len(data['keys'])})  : {', '.join(data['keys'])}")


@freeze_group.command("diff", help="Show drift between freeze file and live vault.")
@click.argument("vault", type=click.Path())
@click.option("--passphrase", "-p", prompt=True, hide_input=True)
@click.option("--json", "as_json", is_flag=True, default=False)
def diff_cmd(vault: str, passphrase: str, as_json: bool) -> None:
    try:
        result = diff_freeze(Path(vault), passphrase)
    except FreezeError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

    if as_json:
        click.echo(json.dumps(result, indent=2))
        return

    if not any([result["added"], result["removed"], result["changed"]]):
        click.echo("No drift detected.")
        return

    for k in result["added"]:
        click.echo(f"  + {k}")
    for k in result["removed"]:
        click.echo(f"  - {k}")
    for k, v in result["changed"].items():
        click.echo(f"  ~ {k}: {v['before']!r} → {v['after']!r}")
