#!/usr/bin/env python3
"""Copy a marker-extracted paper figure into a project's wiki figure folder.

The caller supplies the paper's figure number, not a cache filename. The script
finds the nearest markdown image before the matching ``Figure N:`` caption,
copies it to ``references/wiki/figures/``, and prints the wiki-relative link.
"""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

from PIL import Image


IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Copy marker figure to wiki figures.")
    parser.add_argument("markdown", type=Path, help="Path to marker markdown.md")
    parser.add_argument("wiki_figures_dir", type=Path, help="Project references/wiki/figures dir")
    parser.add_argument("--basename", required=True, help="Canonical paper basename")
    parser.add_argument("--figure", required=True, help="Paper figure label, e.g. 4 or A.1")
    parser.add_argument("--lookback-lines", type=int, default=8)
    return parser.parse_args()


def canonical_suffix(path: Path) -> str:
    with Image.open(path) as image:
        if image.format == "JPEG":
            return ".jpg"
        if image.format == "PNG":
            return ".png"
        if image.format:
            return f".{image.format.lower()}"
    return path.suffix.lower()


def find_source_ref(markdown: str, figure_label: str, lookback_lines: int) -> str:
    lines = markdown.splitlines()
    caption_re = re.compile(rf"\bFigure\s+{re.escape(figure_label)}\s*:", re.IGNORECASE)
    for i, line in enumerate(lines):
        if not caption_re.search(line):
            continue
        start = max(0, i - lookback_lines)
        candidates: list[str] = []
        for nearby in lines[start : i + 1]:
            candidates.extend(IMAGE_RE.findall(nearby))
        if candidates:
            return candidates[-1]
    raise SystemExit(f"figure {figure_label} image reference not found")


def resolve_source_path(markdown_path: Path, source_ref: str) -> Path:
    source_path = (markdown_path.parent / source_ref).resolve()
    if source_path.is_file():
        return source_path

    ref_parts = Path(source_ref).parts
    if len(ref_parts) >= 2 and ref_parts[0] == ref_parts[1]:
        deduped_ref = Path(*ref_parts[1:])
        deduped_path = (markdown_path.parent / deduped_ref).resolve()
        if deduped_path.is_file():
            return deduped_path

    raise SystemExit(f"figure source not found: {source_path}")


def main() -> int:
    args = parse_args()
    markdown_path = args.markdown.expanduser().resolve()
    wiki_figures_dir = args.wiki_figures_dir.expanduser().resolve()
    markdown = markdown_path.read_text(encoding="utf-8", errors="replace")

    source_ref = find_source_ref(markdown, args.figure, args.lookback_lines)
    source_path = resolve_source_path(markdown_path, source_ref)

    suffix = canonical_suffix(source_path)
    wiki_figures_dir.mkdir(parents=True, exist_ok=True)
    dest_path = wiki_figures_dir / f"{args.basename}_fig{args.figure}{suffix}"
    shutil.copy2(source_path, dest_path)
    print(f"figures/{dest_path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
