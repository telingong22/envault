"""CLI commands for vault merging."""

from pathlib import Path

import click

from envault.merge import MergeStrategy, MergeError, merge_vaults


@click.group("merge")
def merge_group() -> None:
    """Merge two encrypted vaults into a single .env file."""


@merge_group.command("run")
@click.argument("base_vault", type=click.Path(exists=True, path_type=Path))
@click.argument("other_vault", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--base-pass",
    prompt="Base vault passphrase",
    hide_input=True,
    help="Passphrase for the base vault.",
)
@click.option(
    "--other-pass",
    prompt="Other vault passphrase",
    hide_input=True,
    help="Passphrase for the other vault.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Destination .env file (default: merged.env next to base vault).",
)
@click.option(
    "--strategy",
    "-s",
    type=click.Choice([s.value for s in MergeStrategy], case_sensitive=False),
    default=MergeStrategy.OURS.value,
    show_default=True,
    help="Conflict resolution strategy.",
)
def run_cmd(
    base_vault: Path,
    other_vault: Path,
    base_pass: str,
    other_pass: str,
    output: Path | None,
    strategy: str,
) -> None:
    """Merge OTHER_VAULT into BASE_VAULT and write a plain .env file."""
    if output is None:
        output = base_vault.parent / "merged.env"

    try:
        result = merge_vaults(
            base_vault,
            other_vault,
            base_pass,
            other_pass,
            output,
            strategy=MergeStrategy(strategy),
        )
    except MergeError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"Merged .env written to: {output}")
    click.echo(result.summary())
    if result.has_conflicts:
        click.echo(
            click.style(
                f"  Conflicting keys ({strategy} strategy applied): "
                + ", ".join(sorted(result.conflicted)),
                fg="yellow",
            )
        )
