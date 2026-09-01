#!/usr/bin/env python3
"""Create a bibcheck run directory and split a .bib file into per-entry files."""

from __future__ import annotations

import argparse
import re
import shutil
from datetime import datetime
from pathlib import Path


ENTRY_START = re.compile(r"@([A-Za-z]+)\s*\{\s*([^,\s]+)\s*,", re.MULTILINE)


def find_entry_end(text: str, start: int) -> int:
    depth = 0
    in_quote = False
    escaped = False

    for index in range(start, len(text)):
        char = text[index]

        if escaped:
            escaped = False
            continue

        if char == "\\":
            escaped = True
            continue

        if char == '"':
            in_quote = not in_quote
            continue

        if in_quote:
            continue

        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index + 1

    raise ValueError(f"Unbalanced braces starting at byte offset {start}")


def sanitize_key(key: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", key).strip("_")
    return safe or "entry"


def split_entries(text: str) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    position = 0

    while True:
        match = ENTRY_START.search(text, position)
        if not match:
            break

        entry_start = match.start()
        key = match.group(2)
        entry_end = find_entry_end(text, match.end() - 1)
        entries.append((key, text[entry_start:entry_end].strip() + "\n"))
        position = entry_end

    return entries


def unique_path(directory: Path, key: str) -> Path:
    stem = sanitize_key(key)
    path = directory / f"{stem}.bib"
    counter = 2

    while path.exists():
        path = directory / f"{stem}_{counter}.bib"
        counter += 1

    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Split a .bib file into one entry per file.")
    parser.add_argument("bib_path", type=Path, help="Input .bib file")
    parser.add_argument("--run-dir", type=Path, default=None, help="Optional output run directory")
    args = parser.parse_args()

    bib_path = args.bib_path.expanduser().resolve()
    if not bib_path.is_file():
        raise SystemExit(f"Bib file not found: {bib_path}")

    run_dir = args.run_dir
    if run_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = bib_path.parent / f"bibcheck_{timestamp}"
    else:
        run_dir = run_dir.expanduser().resolve()

    entries_dir = run_dir / "entries"
    reports_dir = run_dir / "reports"
    entries_dir.mkdir(parents=True, exist_ok=False)
    reports_dir.mkdir(parents=True, exist_ok=True)

    input_copy = run_dir / "input.bib"
    shutil.copy2(bib_path, input_copy)

    text = bib_path.read_text(encoding="utf-8")
    entries = split_entries(text)
    if not entries:
        raise SystemExit(f"No BibTeX entries found in: {bib_path}")

    for key, entry_text in entries:
        unique_path(entries_dir, key).write_text(entry_text, encoding="utf-8")

    print(f"Run directory: {run_dir}")
    print(f"Input copy: {input_copy}")
    print(f"Entries: {len(entries)}")


if __name__ == "__main__":
    main()
