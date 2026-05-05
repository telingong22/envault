"""Command-line interface for envault."""

import sys
import getpass
from pathlib import Path

import click

from envault.vault import Vault


@click.group()
@click.version_option(version="0.1.0", prog_name="envault")
def cli():
    """envault — Lightweight local secrets manager for .env files."""
    pass


@cli.command("lock")
@click.argument("env_file", default=".env", type=click.Path(exists=True))
@click.option(
    "--vault-file",
    default=None,
    help="Path to write the vault file (default: <env_file>.vault)",
)
@click.option(
    "--passphrase",
    envvar="ENVAULT_PASSPHRASE",
    default=None,
    help="Master passphrase (or set ENVAULT_PASSPHRASE env var)",
)
def lock_cmd(env_file, vault_file, passphrase):
    """Encrypt an .env file into a vault."""
    if passphrase is None:
        passphrase = getpass.getpass("Enter master passphrase: ")
        confirm = getpass.getpass("Confirm master passphrase: ")
        if passphrase != confirm:
            click.echo("Error: passphrases do not match.", err=True)
            sys.exit(1)

    env_path = Path(env_file)
    vault_path = Path(vault_file) if vault_file else env_path.with_suffix(".vault")

    vault = Vault(env_path, vault_path)
    vault.lock(passphrase)
    click.echo(f"Locked: {env_path} -> {vault_path}")


@cli.command("unlock")
@click.argument("vault_file", default=".env.vault", type=click.Path(exists=True))
@click.option(
    "--env-file",
    default=None,
    help="Path to write the decrypted .env file (default: <vault_file> without .vault)",
)
@click.option(
    "--passphrase",
    envvar="ENVAULT_PASSPHRASE",
    default=None,
    help="Master passphrase (or set ENVAULT_PASSPHRASE env var)",
)
@click.option(
    "--no-overwrite",
    is_flag=True,
    default=False,
    help="Fail if the .env file already exists.",
)
def unlock_cmd(vault_file, env_file, passphrase, no_overwrite):
    """Decrypt a vault back into a .env file."""
    if passphrase is None:
        passphrase = getpass.getpass("Enter master passphrase: ")

    vault_path = Path(vault_file)
    if env_file:
        env_path = Path(env_file)
    else:
        stem = vault_path.stem if vault_path.suffix == ".vault" else vault_path.name
        env_path = vault_path.parent / stem

    if no_overwrite and env_path.exists():
        click.echo(f"Error: {env_path} already exists. Use without --no-overwrite to overwrite.", err=True)
        sys.exit(1)

    vault = Vault(env_path, vault_path)
    try:
        vault.unlock(passphrase)
        click.echo(f"Unlocked: {vault_path} -> {env_path}")
    except ValueError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
