"""Template rendering: substitute vault secrets into a template string or file."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Union

from envault.vault import Vault


class TemplateError(Exception):
    """Raised when template rendering fails."""


# Matches {{ KEY }} or {{KEY}} — whitespace-tolerant
_PLACEHOLDER = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


def render_string(template: str, secrets: dict[str, str], *, strict: bool = True) -> str:
    """Replace ``{{ KEY }}`` placeholders in *template* with values from *secrets*.

    Parameters
    ----------
    template:
        Raw template text containing ``{{ KEY }}`` placeholders.
    secrets:
        Mapping of variable names to their values.
    strict:
        When *True* (default), raise :class:`TemplateError` if a placeholder
        references a key that is not present in *secrets*.

    Returns
    -------
    str
        Rendered text with all placeholders substituted.
    """
    missing: list[str] = []

    def _replace(match: re.Match) -> str:  # type: ignore[type-arg]
        key = match.group(1)
        if key in secrets:
            return secrets[key]
        missing.append(key)
        return match.group(0)  # leave placeholder intact when not strict

    result = _PLACEHOLDER.sub(_replace, template)

    if strict and missing:
        raise TemplateError(
            f"Template references undefined keys: {', '.join(sorted(missing))}"
        )

    return result


def render_file(
    template_path: Union[str, Path],
    vault_path: Union[str, Path],
    passphrase: str,
    *,
    output_path: Union[str, Path, None] = None,
    strict: bool = True,
) -> str:
    """Render a template file using secrets from a locked vault.

    Parameters
    ----------
    template_path:
        Path to the template file.
    vault_path:
        Path to the ``.vault`` file.
    passphrase:
        Master passphrase used to decrypt the vault.
    output_path:
        If given, write the rendered content to this path.
    strict:
        Passed through to :func:`render_string`.

    Returns
    -------
    str
        Rendered content.
    """
    template_path = Path(template_path)
    if not template_path.exists():
        raise TemplateError(f"Template file not found: {template_path}")

    vault = Vault(vault_path)
    secrets = vault.unlock(passphrase, write=False)

    rendered = render_string(template_path.read_text(encoding="utf-8"), secrets, strict=strict)

    if output_path is not None:
        Path(output_path).write_text(rendered, encoding="utf-8")

    return rendered
