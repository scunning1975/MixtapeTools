#!/usr/bin/env python3
"""Manage neutral read-pdf extracts in the converter cache."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check, pull, or push cached text.md extracts.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check", help="Print cached text.md path or NOT_CACHED.")
    check.add_argument("markdown", type=Path, help="Path to converter cache markdown.md")

    pull = subparsers.add_parser("pull", help="Copy cached text.md to a local _text.md path.")
    pull.add_argument("markdown", type=Path, help="Path to converter cache markdown.md")
    pull.add_argument("local_text", type=Path, help="Destination local _text.md path")

    push = subparsers.add_parser("push", help="Copy local _text.md to cache text.md.")
    push.add_argument("markdown", type=Path, help="Path to converter cache markdown.md")
    push.add_argument("local_text", type=Path, help="Source local _text.md path")

    return parser.parse_args()


def cache_text_path(markdown_path: Path) -> Path:
    markdown_path = markdown_path.expanduser().resolve()
    if not markdown_path.is_file():
        raise SystemExit(f"markdown not found: {markdown_path}")
    if markdown_path.name != "markdown.md":
        raise SystemExit(f"expected markdown.md, got: {markdown_path.name}")
    return markdown_path.parent / "text.md"


def require_nonempty_file(path: Path, label: str) -> Path:
    path = path.expanduser().resolve()
    if not path.is_file():
        raise SystemExit(f"{label} not found: {path}")
    if path.stat().st_size == 0:
        raise SystemExit(f"{label} is empty: {path}")
    return path


def main() -> int:
    args = parse_args()
    cached_text = cache_text_path(args.markdown)

    if args.command == "check":
        print(cached_text if cached_text.is_file() and cached_text.stat().st_size > 0 else "NOT_CACHED")
        return 0

    if args.command == "pull":
        source = require_nonempty_file(cached_text, "cached text.md")
        destination = args.local_text.expanduser().resolve()
        if destination.exists():
            raise SystemExit(f"destination already exists: {destination}")
        if not destination.parent.is_dir():
            raise SystemExit(f"destination parent not found: {destination.parent}")
        shutil.copy2(source, destination)
        print(destination)
        return 0

    if args.command == "push":
        source = require_nonempty_file(args.local_text, "local _text.md")
        cached_text.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, cached_text)
        print(cached_text)
        return 0

    raise SystemExit(f"unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
