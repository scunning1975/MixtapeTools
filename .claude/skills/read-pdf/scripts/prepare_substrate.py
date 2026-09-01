#!/usr/bin/env python3
"""Prepare bounded marker-markdown chunks for agent extraction.

This script is intentionally mechanical: it reads marker's ``markdown.md``,
splits it into bounded source chunks, and writes a manifest that helps agents
navigate the chunks without asking any script to summarize the paper.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


DEFAULT_CHUNK_CHAR_LIMIT = 24000
DEFAULT_TINY_CHUNK_CHAR_LIMIT = 4000
DEFAULT_WORKER_SOURCE_CHAR_LIMIT = 50000

# Heading hygiene: marker sometimes promotes long paragraphs to `#` lines and
# mangles section numbers like `1.6` into `1.[^6]`. We sanitize and guard so
# that the manifest's heading/navigation signal stays useful on non-academic
# PDFs (engineering references, reports with quirky front-matter).
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
HEADING_FOOTNOTE_ARTIFACT_RE = re.compile(r"\[\^([^\]]+)\]")
HEADING_SUP_FOOTNOTE_RE = re.compile(r"<sup>[^<]*</sup>", re.IGNORECASE)
HEADING_EMPHASIS_RE = re.compile(r"\*+")
HEADING_WHITESPACE_RE = re.compile(r"\s+")
HEADING_MAX_LENGTH = 120
HEADING_DISPLAY_CAP = 80
MERGED_HEADING_MAX_PARTS = 2
# Marker's markdown renderer emits `{N}<separator>` between pages when run
# with paginate_output=True. N is the 0-based page index (see convert.py).
# We normalize to 1-based `page-N` strings so the manifest stays
# human-friendly. Anchor 'page-12' means physical page 12 in the source PDF.
PAGE_ANCHOR_RE = re.compile(r"^\{(\d+)\}-{20,}", re.MULTILINE)
FIGURE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\])}>\"']+", re.IGNORECASE)


def sanitize_heading(text: str) -> str:
    # Strip footnote artifacts (`1.[^6]` -> `1.6`), HTML superscript
    # footnote refs (`<sup>1</sup>`), markdown emphasis, and collapse
    # whitespace. Leaves real heading content untouched.
    text = HEADING_FOOTNOTE_ARTIFACT_RE.sub(r"\1", text)
    text = HEADING_SUP_FOOTNOTE_RE.sub("", text)
    text = HEADING_EMPHASIS_RE.sub("", text)
    text = HEADING_WHITESPACE_RE.sub(" ", text).strip()
    return text


def format_merged_heading(parts: list[str]) -> str:
    if len(parts) <= MERGED_HEADING_MAX_PARTS:
        return " / ".join(parts)
    head = " / ".join(parts[:MERGED_HEADING_MAX_PARTS])
    extra = len(parts) - MERGED_HEADING_MAX_PARTS
    return f"{head} (+{extra} more)"


def display_heading(heading: str, cap: int = HEADING_DISPLAY_CAP) -> str:
    if len(heading) <= cap:
        return heading
    return heading[: cap - 3].rstrip() + "..."


@dataclass
class Section:
    heading: str
    level: int
    start_line: int
    end_line: int
    text: str


@dataclass
class Chunk:
    index: int
    heading: str
    path: Path
    start_line: int
    end_line: int
    char_count: int
    sha256: str
    page_anchors: list[str]
    figures: list[str]
    doi_candidates: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create bounded chunk files and manifest for marker markdown."
    )
    parser.add_argument("markdown", type=Path, help="Path to marker markdown.md")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for chunks and manifest; defaults beside markdown.md",
    )
    parser.add_argument(
        "--chunk-char-limit",
        type=int,
        default=DEFAULT_CHUNK_CHAR_LIMIT,
        help=f"Hard max characters per chunk (default {DEFAULT_CHUNK_CHAR_LIMIT})",
    )
    parser.add_argument(
        "--tiny-chunk-char-limit",
        type=int,
        default=DEFAULT_TINY_CHUNK_CHAR_LIMIT,
        help=f"Adjacent chunks below this size may be merged (default {DEFAULT_TINY_CHUNK_CHAR_LIMIT})",
    )
    parser.add_argument(
        "--worker-source-char-limit",
        type=int,
        default=DEFAULT_WORKER_SOURCE_CHAR_LIMIT,
        help=f"Max source characters per worker bundle (default {DEFAULT_WORKER_SOURCE_CHAR_LIMIT})",
    )
    return parser.parse_args()


def slugify(value: str, fallback: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    slug = re.sub(r"-+", "-", slug)
    return (slug[:70].strip("-") or fallback).lower()


def split_sections(lines: list[str]) -> list[Section]:
    starts: list[tuple[int, int, str]] = []
    for i, line in enumerate(lines, start=1):
        match = HEADING_RE.match(line)
        if not match:
            continue
        clean = sanitize_heading(match.group(2))
        # Reject suspiciously long "headings": marker sometimes promotes a
        # full body paragraph (e.g. a mailing-address block) to a `#` line.
        # Treat those as body content so the section boundary isn't false.
        if not clean or len(clean) > HEADING_MAX_LENGTH:
            continue
        starts.append((i, len(match.group(1)), clean))

    if not starts or starts[0][0] != 1:
        starts.insert(0, (1, 0, "front-matter"))

    sections: list[Section] = []
    for pos, (start, level, heading) in enumerate(starts):
        end = starts[pos + 1][0] - 1 if pos + 1 < len(starts) else len(lines)
        text = "".join(lines[start - 1 : end])
        sections.append(Section(heading, level, start, end, text))
    return sections


def split_oversized_section(section: Section, char_limit: int) -> list[Section]:
    if len(section.text) <= char_limit:
        return [section]

    pieces: list[Section] = []
    current_lines: list[str] = []
    current_start = section.start_line
    current_chars = 0

    def flush(end_line: int) -> None:
        nonlocal current_lines, current_start, current_chars
        if not current_lines:
            return
        label = section.heading if not pieces else f"{section.heading} part {len(pieces) + 1}"
        pieces.append(
            Section(label, section.level, current_start, end_line, "".join(current_lines))
        )
        current_lines = []
        current_start = end_line + 1
        current_chars = 0

    for rel_i, line in enumerate(section.text.splitlines(keepends=True), start=0):
        abs_line = section.start_line + rel_i
        line_len = len(line)
        paragraph_break = not line.strip()
        would_exceed = current_lines and current_chars + line_len > char_limit
        if would_exceed and paragraph_break:
            flush(abs_line - 1)
        elif would_exceed and current_chars >= int(char_limit * 0.85):
            flush(abs_line - 1)

        current_lines.append(line)
        current_chars += line_len

        if current_chars >= char_limit:
            flush(abs_line)

    flush(section.end_line)
    return pieces


def merge_tiny_sections(sections: Iterable[Section], tiny_limit: int, hard_limit: int) -> list[Section]:
    merged: list[Section] = []
    pending: Section | None = None
    # Track the original heading parts that were merged into `pending` so the
    # resulting heading can be summarized (first N + "(+K more)") instead of
    # concatenating every subsection name into a multi-hundred-char blob.
    pending_parts: list[str] = []

    for section in sections:
        if pending is None:
            pending = section
            pending_parts = [section.heading]
            continue

        combined_len = len(pending.text) + len(section.text)
        if len(pending.text) < tiny_limit and combined_len <= hard_limit:
            pending_parts.append(section.heading)
            pending = Section(
                heading=format_merged_heading(pending_parts),
                level=min(pending.level, section.level),
                start_line=pending.start_line,
                end_line=section.end_line,
                text=pending.text + section.text,
            )
        else:
            merged.append(pending)
            pending = section
            pending_parts = [section.heading]

    if pending is not None:
        merged.append(pending)
    return merged


def collect_page_markers(lines: list[str]) -> list[tuple[int, int]]:
    # Return (line_number, page_id) for every paginate_output marker line.
    # 1-based line numbers to match Section.start_line semantics.
    markers: list[tuple[int, int]] = []
    for i, line in enumerate(lines, start=1):
        m = PAGE_ANCHOR_RE.match(line)
        if m:
            markers.append((i, int(m.group(1))))
    return markers


def pages_for_range(
    markers: list[tuple[int, int]], start_line: int, end_line: int
) -> list[str]:
    # Page anchors a chunk overlaps: the most recent marker at-or-before
    # start_line (carryover, so chunks that begin mid-page still get a page
    # number), plus every marker inside [start_line, end_line].
    page_ids: set[int] = set()
    carryover: int | None = None
    for line_no, page_id in markers:
        if line_no <= start_line:
            carryover = page_id
        elif line_no <= end_line:
            page_ids.add(page_id)
        else:
            break
    if carryover is not None:
        page_ids.add(carryover)
    return [f"page-{pid + 1}" for pid in sorted(page_ids)]


def metadata_for_chunk(text: str) -> tuple[list[str], list[str], str]:
    figures = sorted(set(FIGURE_RE.findall(text)))
    doi_candidates = sorted(set(match.rstrip(".,;") for match in DOI_RE.findall(text)))
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return figures, doi_candidates, digest


def write_chunks(
    sections: list[Section],
    chunks_dir: Path,
    page_markers: list[tuple[int, int]],
) -> list[Chunk]:
    chunks_dir.mkdir(parents=True, exist_ok=True)
    for old_chunk in chunks_dir.glob("chunk_*.md"):
        old_chunk.unlink()

    chunks: list[Chunk] = []
    for index, section in enumerate(sections, start=1):
        slug = slugify(section.heading, f"chunk-{index:03d}")
        path = chunks_dir / f"chunk_{index:03d}-{slug}.md"
        figures, doi_candidates, digest = metadata_for_chunk(section.text)
        page_anchors = pages_for_range(
            page_markers, section.start_line, section.end_line
        )
        path.write_text(section.text, encoding="utf-8")
        chunks.append(
            Chunk(
                index=index,
                heading=section.heading,
                path=path,
                start_line=section.start_line,
                end_line=section.end_line,
                char_count=len(section.text),
                sha256=digest,
                page_anchors=page_anchors,
                figures=figures,
                doi_candidates=doi_candidates,
            )
        )
    return chunks


def bundle_chunks(chunks: list[Chunk], source_limit: int) -> list[dict[str, object]]:
    bundles: list[dict[str, object]] = []
    current: list[Chunk] = []
    current_chars = 0

    def flush() -> None:
        nonlocal current, current_chars
        if not current:
            return
        position = "body"
        if not bundles:
            position = "front_matter"
        bundles.append(
            {
                "bundle_id": f"bundle_{len(bundles) + 1:03d}",
                "position": position,
                "chunk_indexes": [chunk.index for chunk in current],
                "chunk_paths": [str(chunk.path) for chunk in current],
                "char_count": current_chars,
                "headings": [display_heading(chunk.heading) for chunk in current],
            }
        )
        current = []
        current_chars = 0

    for chunk in chunks:
        if current and current_chars + chunk.char_count > source_limit:
            flush()
        current.append(chunk)
        current_chars += chunk.char_count
    flush()

    if len(bundles) > 1:
        bundles[-1]["position"] = "back_matter"
    elif len(bundles) == 1:
        bundles[0]["position"] = "full_paper"
    return bundles


def main() -> int:
    args = parse_args()
    markdown_path = args.markdown.expanduser().resolve()
    if not markdown_path.exists():
        raise SystemExit(f"markdown not found: {markdown_path}")

    output_dir = (
        args.output_dir.expanduser().resolve()
        if args.output_dir
        else markdown_path.parent / "substrate"
    )
    chunks_dir = output_dir / "chunks"
    manifest_path = output_dir / "manifest.json"
    output_dir.mkdir(parents=True, exist_ok=True)

    text = markdown_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines(keepends=True)
    page_markers = collect_page_markers(lines)
    sections = split_sections(lines)

    bounded_sections: list[Section] = []
    for section in sections:
        bounded_sections.extend(split_oversized_section(section, args.chunk_char_limit))
    bounded_sections = merge_tiny_sections(
        bounded_sections, args.tiny_chunk_char_limit, args.chunk_char_limit
    )

    chunks = write_chunks(bounded_sections, chunks_dir, page_markers)
    bundles = bundle_chunks(chunks, args.worker_source_char_limit)

    manifest = {
        "schema_version": 1,
        "source_markdown": str(markdown_path),
        "source_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "source_line_count": len(lines),
        "source_char_count": len(text),
        "chunk_char_limit": args.chunk_char_limit,
        "worker_source_char_limit": args.worker_source_char_limit,
        "chunks_dir": str(chunks_dir),
        "chunks": [
            {
                "index": chunk.index,
                "path": str(chunk.path),
                "heading": chunk.heading,
                "line_range": [chunk.start_line, chunk.end_line],
                "char_count": chunk.char_count,
                "sha256": chunk.sha256,
                "page_anchors": chunk.page_anchors,
                "figures": chunk.figures,
                "doi_candidates": chunk.doi_candidates,
            }
            for chunk in chunks
        ],
        "worker_bundles": bundles,
        "doi_candidates": sorted({doi for chunk in chunks for doi in chunk.doi_candidates}),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(manifest_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
