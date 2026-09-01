#!/usr/bin/env python3
"""Run the DOI → CrossRef → OpenAlex fetch cascade for a single paper.

Reads the parsed `## Bibliographic metadata` block via CLI flags, queries
each source in order, and emits a JSON result to stdout:

    {
      "stem": "Deryugina_etal_2019_AER",
      "tier": 1 | 2 | 3,
      "source": "doi-direct" | "crossref" | "openalex" | "fallback-needed",
      "bibtex": "@article{...}" | null,
      "match_signals": {                     # tier-2 only
          "title_score": 0.94,
          "year_off_by_one": false,
          "author_ok": true
      },
      "rejections": [{"source": "...", "candidate": "...", "reason": "..."}]
    }

Tier 1 = DOI direct (auto-append). Tier 2 = CrossRef / OpenAlex fuzzy match
(auto-append, flag for spot-check). Tier 3 = no source agreed — the caller
constructs an unverified @misc/@article/@techreport from metadata and blocks
for user approval.

The script never decides whether to append. It only fetches and validates.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.parse
from difflib import SequenceMatcher
from typing import Any

HTTP_TIMEOUT_SEC = 10
TITLE_MATCH_THRESHOLD = 0.85
USER_AGENT = "bib-update/1.0 (https://github.com/scunning1975/MixtapeTools)"

VENUE_TYPE_TO_BIBTEX = {
    "journal": "article",
    "working_paper": "techreport",
    "book_chapter": "incollection",
    "other": "misc",
}


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


def http_get(url: str, accept: str = "application/json") -> tuple[int, str]:
    """GET a URL via curl. Returns (status, body). Curl errors → (0, '')."""
    try:
        proc = subprocess.run(
            [
                "curl",
                "-sSL",  # silent, show errors, follow redirects
                "-H",
                f"Accept: {accept}",
                "-H",
                f"User-Agent: {USER_AGENT}",
                "--max-time",
                str(HTTP_TIMEOUT_SEC),
                "-w",
                "\n__HTTP_STATUS__:%{http_code}",
                url,
            ],
            capture_output=True,
            text=True,
            timeout=HTTP_TIMEOUT_SEC + 5,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return 0, ""
    if proc.returncode != 0:
        return 0, ""
    body = proc.stdout
    status = 0
    marker = "\n__HTTP_STATUS__:"
    idx = body.rfind(marker)
    if idx >= 0:
        try:
            status = int(body[idx + len(marker) :].strip())
        except ValueError:
            status = 0
        body = body[:idx]
    return status, body


def fetch_bibtex_for_doi(doi: str) -> str | None:
    """Content-negotiate a DOI for a BibTeX record. Returns text or None."""
    doi = doi.strip().lstrip("doi:").strip()
    if not doi:
        return None
    url = f"https://doi.org/{urllib.parse.quote(doi, safe='/')}"
    status, body = http_get(url, accept="application/x-bibtex")
    body = body.strip()
    if status == 200 and body.startswith("@"):
        return body
    return None


# ---------------------------------------------------------------------------
# Normalization / matching
# ---------------------------------------------------------------------------


def normalize_title(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def title_score(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize_title(a), normalize_title(b)).ratio()


def authors_match(claimed_last: str, candidate_last: str) -> bool:
    a = claimed_last.strip().lower()
    b = candidate_last.strip().lower()
    return bool(a) and bool(b) and (a == b or a in b or b in a)


# ---------------------------------------------------------------------------
# Filename parsing for three-way agreement
# ---------------------------------------------------------------------------


def parse_stem(stem: str) -> dict[str, str | int | None]:
    """Parse `Author_etal_Year_Venue` or `Last1_Last2_Year_Venue` style stems.

    Returns {first_author, year} where possible; either may be None if the
    stem does not match the convention.
    """
    parts = stem.split("_")
    year = None
    year_idx = None
    for i, p in enumerate(parts):
        if re.fullmatch(r"(19|20)\d{2}", p):
            year = int(p)
            year_idx = i
            break
    first_author = parts[0] if parts and year_idx is not None and year_idx > 0 else None
    return {"first_author": first_author, "year": year}


# ---------------------------------------------------------------------------
# Three-signal match test
# ---------------------------------------------------------------------------


def evaluate_candidate(
    *,
    claimed_year: int,
    claimed_first_author: str,
    claimed_title: str,
    cand_year: int | None,
    cand_first_author: str,
    cand_title: str,
    stem_year: int | None,
    stem_first_author: str | None,
) -> tuple[bool, dict[str, Any], str | None]:
    """Apply 3-signal + three-way agreement. Returns (passed, signals, reject_reason)."""
    signals: dict[str, Any] = {
        "title_score": round(title_score(claimed_title, cand_title), 3),
        "year_off_by_one": False,
        "author_ok": False,
    }

    # Title
    if signals["title_score"] < TITLE_MATCH_THRESHOLD:
        return False, signals, f"title score {signals['title_score']:.2f} < {TITLE_MATCH_THRESHOLD}"

    # Year ±1
    if cand_year is None:
        return False, signals, "candidate has no year"
    year_diff = abs(cand_year - claimed_year)
    if year_diff > 1:
        return False, signals, f"year mismatch ({cand_year} vs {claimed_year})"
    signals["year_off_by_one"] = year_diff == 1

    # First author
    signals["author_ok"] = authors_match(claimed_first_author, cand_first_author)
    if not signals["author_ok"]:
        return False, signals, f"author mismatch ({cand_first_author} vs {claimed_first_author})"

    # Three-way agreement (filename axis): year + first author must agree across
    # filename, metadata block, and API candidate. Filename axis is optional —
    # if the stem doesn't parse cleanly, skip it.
    if stem_year is not None and abs(stem_year - cand_year) > 1:
        return False, signals, f"stem year {stem_year} disagrees with candidate {cand_year}"
    if stem_first_author and not authors_match(stem_first_author, cand_first_author):
        return False, signals, f"stem author {stem_first_author} disagrees with candidate {cand_first_author}"

    return True, signals, None


# ---------------------------------------------------------------------------
# Source queries
# ---------------------------------------------------------------------------


def crossref_candidates(title: str, first_author_last: str) -> list[dict[str, Any]]:
    qs = urllib.parse.urlencode(
        {"query.title": title, "query.author": first_author_last, "rows": "5"}
    )
    url = f"https://api.crossref.org/works?{qs}"
    status, body = http_get(url)
    if status != 200 or not body:
        return []
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return []
    items = data.get("message", {}).get("items", []) or []
    out = []
    for it in items:
        title_list = it.get("title") or []
        author_list = it.get("author") or []
        # Year resolution: prefer published-print, fall back to issued, then created
        year = None
        for key in ("published-print", "published-online", "issued", "created"):
            parts = (it.get(key) or {}).get("date-parts") or []
            if parts and parts[0] and parts[0][0]:
                year = parts[0][0]
                break
        out.append(
            {
                "doi": it.get("DOI"),
                "title": title_list[0] if title_list else "",
                "year": year,
                "first_author_last": (author_list[0] or {}).get("family", "") if author_list else "",
                "raw": it,
            }
        )
    return out


def openalex_candidates(title: str, first_author_last: str) -> list[dict[str, Any]]:
    qs = urllib.parse.urlencode(
        {
            "search": title,
            "filter": f"authorships.author.display_name.search:{first_author_last}",
            "per-page": "5",
        }
    )
    url = f"https://api.openalex.org/works?{qs}"
    status, body = http_get(url)
    if status != 200 or not body:
        return []
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return []
    items = data.get("results", []) or []
    out = []
    for it in items:
        authorships = it.get("authorships") or []
        first_last = ""
        if authorships:
            display = (authorships[0].get("author") or {}).get("display_name") or ""
            first_last = display.split()[-1] if display else ""
        doi = it.get("doi") or ""
        if doi.startswith("https://doi.org/"):
            doi = doi[len("https://doi.org/") :]
        out.append(
            {
                "doi": doi or None,
                "title": it.get("title") or "",
                "year": it.get("publication_year"),
                "first_author_last": first_last,
                "raw": it,
            }
        )
    return out


# ---------------------------------------------------------------------------
# BibTeX construction (used when OpenAlex hit has no DOI)
# ---------------------------------------------------------------------------


def bibtex_from_openalex(stem: str, venue_type: str, oa: dict[str, Any]) -> str:
    entry_type = VENUE_TYPE_TO_BIBTEX.get(venue_type, "misc")
    authorships = oa.get("authorships") or []
    authors = " and ".join(
        (a.get("author") or {}).get("display_name", "") for a in authorships if a.get("author")
    )
    title = oa.get("title") or ""
    year = oa.get("publication_year") or ""
    host = (oa.get("host_venue") or {}).get("display_name") or oa.get("primary_location", {}).get(
        "source", {}
    ).get("display_name", "")
    lines = [f"@{entry_type}{{{stem},"]
    if authors:
        lines.append(f"  author = {{{authors}}},")
    if title:
        lines.append(f"  title  = {{{title}}},")
    if year:
        lines.append(f"  year   = {{{year}}},")
    if host:
        field = "institution" if entry_type == "techreport" else "journal"
        lines.append(f"  {field} = {{{host}}},")
    lines.append("}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Citation key rewriting
# ---------------------------------------------------------------------------


KEY_RE = re.compile(r"^(@[A-Za-z]+\s*\{\s*)([^,\s]+)(\s*,)", re.MULTILINE)


def rewrite_key(bibtex: str, stem: str) -> str:
    return KEY_RE.sub(lambda m: f"{m.group(1)}{stem}{m.group(3)}", bibtex, count=1)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    p = argparse.ArgumentParser(description="Fetch BibTeX via DOI → CrossRef → OpenAlex cascade.")
    p.add_argument("stem", help="Filename stem (used as citation key)")
    p.add_argument("--doi", default="", help="DOI from metadata block (empty/null OK)")
    p.add_argument("--first-author", required=True, help="First author's last name")
    p.add_argument("--title", required=True, help="Verbatim paper title")
    p.add_argument("--year", required=True, type=int, help="Year of publication")
    p.add_argument("--venue", default="", help="Venue (journal/series/etc.)")
    p.add_argument(
        "--venue-type",
        default="journal",
        choices=list(VENUE_TYPE_TO_BIBTEX.keys()),
        help="Maps to BibTeX entry type when OpenAlex has no DOI",
    )
    args = p.parse_args()

    stem_parsed = parse_stem(args.stem)
    rejections: list[dict[str, str]] = []

    # Source 0 — DOI direct
    if args.doi and args.doi.lower() not in ("null", "none", ""):
        bib = fetch_bibtex_for_doi(args.doi)
        if bib:
            result = {
                "stem": args.stem,
                "tier": 1,
                "source": "doi-direct",
                "bibtex": rewrite_key(bib, args.stem),
                "match_signals": None,
                "rejections": rejections,
            }
            print(json.dumps(result, indent=2))
            return
        rejections.append({"source": "doi-direct", "candidate": args.doi, "reason": "no @-record returned"})

    # Source 1 — CrossRef
    for cand in crossref_candidates(args.title, args.first_author):
        passed, signals, reason = evaluate_candidate(
            claimed_year=args.year,
            claimed_first_author=args.first_author,
            claimed_title=args.title,
            cand_year=cand["year"],
            cand_first_author=cand["first_author_last"],
            cand_title=cand["title"],
            stem_year=stem_parsed["year"],
            stem_first_author=stem_parsed["first_author"],
        )
        if not passed:
            rejections.append(
                {"source": "crossref", "candidate": cand.get("doi") or cand["title"][:60], "reason": reason or ""}
            )
            continue
        # Passed — content-negotiate this candidate's DOI
        if cand["doi"]:
            bib = fetch_bibtex_for_doi(cand["doi"])
            if bib:
                result = {
                    "stem": args.stem,
                    "tier": 2,
                    "source": "crossref",
                    "bibtex": rewrite_key(bib, args.stem),
                    "match_signals": signals,
                    "rejections": rejections,
                }
                print(json.dumps(result, indent=2))
                return
            rejections.append(
                {"source": "crossref", "candidate": cand["doi"], "reason": "DOI negotiation returned empty"}
            )

    # Source 2 — OpenAlex
    for cand in openalex_candidates(args.title, args.first_author):
        passed, signals, reason = evaluate_candidate(
            claimed_year=args.year,
            claimed_first_author=args.first_author,
            claimed_title=args.title,
            cand_year=cand["year"],
            cand_first_author=cand["first_author_last"],
            cand_title=cand["title"],
            stem_year=stem_parsed["year"],
            stem_first_author=stem_parsed["first_author"],
        )
        if not passed:
            rejections.append(
                {"source": "openalex", "candidate": cand.get("doi") or cand["title"][:60], "reason": reason or ""}
            )
            continue
        if cand["doi"]:
            bib = fetch_bibtex_for_doi(cand["doi"])
            if bib:
                result = {
                    "stem": args.stem,
                    "tier": 2,
                    "source": "openalex",
                    "bibtex": rewrite_key(bib, args.stem),
                    "match_signals": signals,
                    "rejections": rejections,
                }
                print(json.dumps(result, indent=2))
                return
            rejections.append(
                {"source": "openalex", "candidate": cand["doi"], "reason": "DOI negotiation returned empty"}
            )
        # No DOI — construct from OpenAlex JSON directly
        bib = bibtex_from_openalex(args.stem, args.venue_type, cand["raw"])
        result = {
            "stem": args.stem,
            "tier": 2,
            "source": "openalex",
            "bibtex": bib,
            "match_signals": signals,
            "rejections": rejections,
        }
        print(json.dumps(result, indent=2))
        return

    # All sources exhausted — caller must construct from metadata and block for approval
    result = {
        "stem": args.stem,
        "tier": 3,
        "source": "fallback-needed",
        "bibtex": None,
        "match_signals": None,
        "rejections": rejections,
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    sys.exit(main())
