"""CLI commands for importing secrets into a vault."""
from __future__ import annotations

from pathlib import Path

import click

from envault.import_env import ImportError as EnvImportError
from envault.import_env import import_into_vault


@click.group("import")
def import_group() -> None:
    """Import secrets from external files into a vault."""


@import_group.command("run")
@click.argument("source", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--vault",
    "vault_path",
    default=".env.vault",
    show_default=True,
    type=click.Path(path_type=Path),
    help="Destination vault file.",
)
@click.option(
    "--passphrase",
    prompt=True,
    hide_input=True,
    help="Master passphrase for the vault.",
)
@click.option(
    "--format",
    "fmt",
    default="dotenv",
    show_default=True,
    type=click.Choice(["dotenv", "json"], case_sensitive=False),
    help="Format of the source file.",
)
@click.option(
    "--merge",
    is_flag=True,
    default=False,
    help="Merge with existing vault contents instead of overwriting.",
)
def run_cmd(
    source: Path,
    vault_path: Path,
    passphrase: str,
    fmt: str,
    merge: bool,
) -> None:
    """Import secrets from SOURCE into the vault.

    SOURCE can be a .env file or a JSON file.
    """
    try:
        result = import_into_vault(
            source=source,
            vault_path=vault_path,
            passphrase=passphrase,
            fmt=fmt,
            merge=merge,
        )
    except EnvImportError as exc:
        raise click.ClickException(str(exc)) from exc

    action = "Merged" if merge else "Imported"
    click.echo(
        f"{action} {len(result)} key(s) from '{source}' into '{vault_path}'."
    )
