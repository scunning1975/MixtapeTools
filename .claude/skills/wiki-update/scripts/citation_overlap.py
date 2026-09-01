#!/usr/bin/env python3
"""Find mechanical citation overlaps between a new paper and references.bib.

This script emits candidates only. It does not decide scholarly relevance.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\])}>\"']+", re.IGNORECASE)
BIB_ENTRY_RE = re.compile(r"@\w+\s*\{\s*([^,]+),([\s\S]*?)(?=\n@\w+\s*\{|\Z)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Emit citation-overlap candidates.")
    parser.add_argument("markdown", type=Path, help="New paper marker markdown.md")
    parser.add_argument("bibtex", type=Path, help="references/references.bib")
    parser.add_argument("--output", type=Path, required=True, help="Output JSON path")
    parser.add_argument("--max-candidates", type=int, default=50)
    return parser.parse_args()


def normalize_text(value: str) -> str:
    value = re.sub(r"[{}\\]", "", value or "").lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def parse_bib(path: Path) -> list[dict[str, str]]:
    if not path.exists() or not path.read_text(encoding="utf-8", errors="ignore").strip():
        return []
    text = path.read_text(encoding="utf-8", errors="ignore")
    entries: list[dict[str, str]] = []
    for match in BIB_ENTRY_RE.finditer(text):
        key = match.group(1).strip()
        body = match.group(2)
        fields = {"key": key}
        fields.update(parse_bib_fields(body))
        entries.append(fields)
    return entries


def parse_bib_fields(body: str) -> dict[str, str]:
    """Parse simple BibTeX fields while preserving nested braces."""
    fields: dict[str, str] = {}
    i = 0
    n = len(body)

    while i < n:
        while i < n and not (body[i].isalpha() or body[i] == "_"):
            i += 1
        start = i
        while i < n and (body[i].isalnum() or body[i] in "_-"):
            i += 1
        name = body[start:i].strip().lower()
        if not name:
            break
        while i < n and body[i].isspace():
            i += 1
        if i >= n or body[i] != "=":
            continue
        i += 1
        while i < n and body[i].isspace():
            i += 1
        if i >= n:
            break

        if body[i] == "{":
            i += 1
            value_start = i
            depth = 1
            while i < n and depth:
                if body[i] == "{":
                    depth += 1
                elif body[i] == "}":
                    depth -= 1
                i += 1
            value = body[value_start : i - 1]
        elif body[i] == '"':
            i += 1
            value_start = i
            escaped = False
            while i < n:
                char = body[i]
                if char == '"' and not escaped:
                    break
                escaped = char == "\\" and not escaped
                if char != "\\":
                    escaped = False
                i += 1
            value = body[value_start:i]
            if i < n and body[i] == '"':
                i += 1
        else:
            value_start = i
            while i < n and body[i] not in ",\n":
                i += 1
            value = body[value_start:i]

        fields[name] = value.strip()
        while i < n and body[i] != ",":
            i += 1
        if i < n and body[i] == ",":
            i += 1

    return fields


def candidate_reference_text(markdown: str) -> str:
    lower = markdown.lower()
    starts = [lower.rfind("\n# references"), lower.rfind("\n## references")]
    start = max(starts)
    if start == -1:
        start = max(lower.rfind("\nreferences"), int(len(markdown) * 0.75))
    return markdown[start:]


def score_match(label: str) -> int:
    return {
        "doi_exact": 100,
        "bib_key_string_seen": 80,
        "title_exact_normalized": 75,
        "title_substring_normalized": 60,
        "author_year_exact": 50,
    }.get(label, 10)


def meaningful_title_prefix(title: str) -> str:
    words = [word for word in title.split() if len(word) > 3]
    return " ".join(words[:6])


def find_matches(markdown: str, entries: list[dict[str, str]]) -> list[dict[str, object]]:
    refs = candidate_reference_text(markdown)
    refs_norm = normalize_text(refs)
    dois_seen = {doi.rstrip(".,;").lower() for doi in DOI_RE.findall(refs)}
    matches: dict[str, dict[str, object]] = {}

    for entry in entries:
        labels: set[str] = set()
        key = entry.get("key", "")
        title = normalize_text(entry.get("title", ""))
        year = normalize_text(entry.get("year", ""))
        authors = normalize_text(entry.get("author", ""))
        doi = entry.get("doi", "").rstrip(".,;").lower()

        if doi and doi in dois_seen:
            labels.add("doi_exact")
        if key and key.lower() in refs.lower():
            labels.add("bib_key_string_seen")
        if title and title in refs_norm:
            labels.add("title_exact_normalized")
        else:
            title_prefix = meaningful_title_prefix(title)
            if title_prefix and len(title_prefix) > 30 and title_prefix in refs_norm:
                labels.add("title_substring_normalized")
        if year and authors:
            first_author = authors.split(" and ")[0].split()[-1]
            if first_author and f"{first_author} {year}" in refs_norm:
                labels.add("author_year_exact")

        if labels:
            best_score = max(score_match(label) for label in labels)
            matches[key] = {
                "bib_key": key,
                "title": entry.get("title"),
                "year": entry.get("year"),
                "doi": entry.get("doi"),
                "match_labels": sorted(labels),
                "priority_score": best_score,
            }

    return sorted(matches.values(), key=lambda item: (-int(item["priority_score"]), str(item["bib_key"])))


def main() -> int:
    args = parse_args()
    markdown = args.markdown.expanduser().read_text(encoding="utf-8", errors="ignore")
    entries = parse_bib(args.bibtex.expanduser())
    candidates = find_matches(markdown, entries)[: args.max_candidates]
    output = {
        "schema_version": 1,
        "source_markdown": str(args.markdown.expanduser().resolve()),
        "bibtex": str(args.bibtex.expanduser().resolve()),
        "candidate_count": len(candidates),
        "candidates": candidates,
    }
    args.output.expanduser().parent.mkdir(parents=True, exist_ok=True)
    args.output.expanduser().write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(args.output.expanduser())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
