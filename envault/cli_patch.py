"""CLI commands for patching a vault with new key/value pairs."""

from __future__ import annotations

from pathlib import Path

import click

from envault.env_patch import PatchError, apply_patch


@click.group("patch")
def patch_group() -> None:
    """Apply key=value patches to a vault."""


@patch_group.command("run")
@click.argument("vault_path", type=click.Path(exists=True, path_type=Path))
@click.option("--passphrase", "-p", required=True, help="Master passphrase.")
@click.option(
    "--set",
    "pairs",
    multiple=True,
    metavar="KEY=VALUE",
    help="Key/value pair to patch (repeatable).",
)
@click.option(
    "--file",
    "patch_file",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to a .env-style patch file.",
)
@click.option(
    "--no-overwrite",
    is_flag=True,
    default=False,
    help="Skip keys that already exist in the vault.",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    default=False,
    help="Output result as JSON.",
)
def run_cmd(
    vault_path: Path,
    passphrase: str,
    pairs: tuple[str, ...],
    patch_file: Path | None,
    no_overwrite: bool,
    as_json: bool,
) -> None:
    """Patch VAULT_PATH with supplied key/value pairs."""
    patch_text = ""
    if patch_file:
        patch_text += patch_file.read_text()
    if pairs:
        patch_text += "\n" + "\n".join(pairs)

    if not patch_text.strip():
        raise click.UsageError("Provide at least one --set KEY=VALUE or --file.")

    try:
        result = apply_patch(
            vault_path,
            passphrase,
            patch_text,
            overwrite=not no_overwrite,
        )
    except PatchError as exc:
        raise click.ClickException(str(exc)) from exc

    if as_json:
        import json
        click.echo(json.dumps(result.as_dict(), indent=2))
        return

    click.echo(f"Patched vault: {result.vault_path}")
    if result.applied:
        click.echo(f"  Applied : {', '.join(result.applied)}")
    if result.skipped:
        click.echo(f"  Skipped : {', '.join(result.skipped)}")
