"""Tag management for vault files — attach, remove, and filter by tags."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

TAGS_SUFFIX = ".tags.json"


class TagError(Exception):
    """Raised when a tag operation fails."""


def _tags_path(vault_path: Path) -> Path:
    return vault_path.with_name(vault_path.name + TAGS_SUFFIX)


def _load_tags(vault_path: Path) -> List[str]:
    tp = _tags_path(vault_path)
    if not tp.exists():
        return []
    try:
        data = json.loads(tp.read_text())
        if not isinstance(data, list):
            raise TagError(f"Corrupt tags file: {tp}")
        return [str(t) for t in data]
    except json.JSONDecodeError as exc:
        raise TagError(f"Corrupt tags file: {tp}") from exc


def _save_tags(vault_path: Path, tags: List[str]) -> None:
    _tags_path(vault_path).write_text(json.dumps(sorted(set(tags)), indent=2))


def add_tag(vault_path: Path, tag: str) -> List[str]:
    """Add *tag* to *vault_path*.  Returns the updated tag list."""
    if not vault_path.exists():
        raise TagError(f"Vault not found: {vault_path}")
    tag = tag.strip()
    if not tag:
        raise TagError("Tag must not be empty.")
    tags = _load_tags(vault_path)
    if tag not in tags:
        tags.append(tag)
    _save_tags(vault_path, tags)
    return sorted(set(tags))


def remove_tag(vault_path: Path, tag: str) -> List[str]:
    """Remove *tag* from *vault_path*.  Returns the updated tag list."""
    tags = _load_tags(vault_path)
    tags = [t for t in tags if t != tag]
    _save_tags(vault_path, tags)
    return tags


def list_tags(vault_path: Path) -> List[str]:
    """Return tags associated with *vault_path*."""
    return _load_tags(vault_path)


def find_vaults_by_tag(directory: Path, tag: str) -> List[Path]:
    """Return vault paths inside *directory* that carry *tag*."""
    results: List[Path] = []
    for tags_file in directory.glob(f"*{TAGS_SUFFIX}"):
        vault_candidate = tags_file.with_name(
            tags_file.name[: -len(TAGS_SUFFIX)]
        )
        try:
            data = json.loads(tags_file.read_text())
            if isinstance(data, list) and tag in data and vault_candidate.exists():
                results.append(vault_candidate)
        except (json.JSONDecodeError, OSError):
            continue
    return sorted(results)
