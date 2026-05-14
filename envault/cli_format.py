"""CLI commands for the env-format feature."""
from __future__ import annotations

from pathlib import Path

import click

from envault.env_format import FormatError, format_vault


@click.group("format")
def format_group() -> None:
    """Format and normalise vault contents."""


@format_group.command("run")
@click.argument("vault_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--passphrase",
    "-p",
    prompt=True,
    hide_input=True,
    help="Master passphrase for the vault.",
)
@click.option("--json", "as_json", is_flag=True, default=False, help="Output JSON.")
def run_cmd(vault_path: Path, passphrase: str, as_json: bool) -> None:
    """Format the .env contents stored in VAULT_PATH."""
    try:
        result = format_vault(vault_path, passphrase)
    except FormatError as exc:
        raise click.ClickException(str(exc)) from exc

    if as_json:
        import json

        click.echo(json.dumps(result.as_dict(), indent=2))
        return

    if result.changed:
        click.echo(f"Formatted {vault_path}")
        click.echo(f"  Lines before : {result.lines_before}")
        click.echo(f"  Lines after  : {result.lines_after}")
        if result.changes:
            click.echo("  Changes:")
            for change in result.changes:
                click.echo(f"    - {change}")
    else:
        click.echo(f"Already formatted: {vault_path}")
