---
name: bib-update
description: >-
  Assemble or refresh `references/references.bib` from per-paper
  `## Bibliographic metadata` blocks in `references/raw/<basename>_text.md`.
  Cascade: DOI direct fetch → CrossRef title+author → OpenAlex →
  LLM-from-metadata fallback. Idempotent — safe to re-run; only appends entries
  whose citation key is missing. Use `--rebuild-bib` to regenerate from scratch.
  Runnable standalone (no wiki required) or called automatically as the final
  step of `/wiki-update`.
allowed-tools: Read, Edit, Write, Glob, Grep, Bash(ls*), Bash(curl:*), Bash(mkdir:*), Bash(pdftotext:*), Bash(pdftoppm:*), Bash(python3:*), Bash(~/.claude/skills/bib-update/scripts/fetch_bibtex.py:*)
argument-hint: [--rebuild-bib]
---

# bib-update: Assemble or refresh references/references.bib

Scans `references/raw/` for per-paper `_text.md` extracts, reads each paper's `## Bibliographic metadata` block, fetches a verified BibTeX entry via a cascade of sources, and appends to `references/references.bib`. Idempotent: papers already present in `.bib` are skipped.

This is a **maintenance companion** to `/bibcheck`, not a replacement. `/bib-update` assembles and refreshes the project BibTeX file from paper metadata; `/bibcheck` audits an existing `.bib` for correctness against canonical sources.

## When this skill is invoked

- By the user directly (standalone), to assemble or refresh `.bib` without re-ingesting PDFs.
- Automatically, as the final step of `/wiki-update`.

## Default mode (append-only)

1. Check that `references/raw/` exists. If not, stop: "No `references/raw/` directory found in the current working directory."
2. Scan `references/raw/` for files matching `*_text.md`. Collect their basename stems (e.g., `Deryugina_etal_2019_AER` from `Deryugina_etal_2019_AER_text.md`). Exclude `log.md` and any file whose name ends in `_log.md`.
3. Parse each `_text.md` for a valid `## Bibliographic metadata` block. If the block is missing or malformed and `references/raw/<stem>.pdf` exists, send that stem through the **bootstrap fallback** (see below) rather than skipping. If the block is missing or malformed and no matching PDF exists, warn and skip that paper.
4. Also scan `references/raw/` for PDF files (`*.pdf`) with no corresponding `_text.md`. These go through the **bootstrap fallback** to extract a minimal metadata block before entering the fetch cascade.
5. If `references/references.bib` exists, read it and parse out existing citation keys — lines matching `@\w+\{<key>,`. If the file does not exist, create it (empty).
6. For each stem (from `_text.md` or bootstrap), skip if its citation key already appears in `.bib`. Queue the rest for the fetch cascade.
7. If the queue is empty, report "All entries up to date — nothing to add." and exit.
8. Run the fetch cascade (see below) for each queued stem. Collect results, then surface the tier report and append.

## Rebuild mode (--rebuild-bib)

When `--rebuild-bib` is passed:

1. Scan `references/raw/` for `*_text.md` files and bare PDFs, collect stems (same exclusions as above).
2. Confirm with user: "This will overwrite `references/references.bib` with entries for N papers. Proceed? (yes/no)"
3. On yes, run the fetch cascade for all N stems (bootstrapping bare PDFs first).
4. Hard-stop at each tier-3 entry for per-entry approval before writing.
5. Write all accepted entries to `references/references.bib`, overwriting.

## Bootstrap fallback (missing metadata or bare PDF)

When a PDF in `references/raw/` has no corresponding `_text.md`, or the corresponding `_text.md` is missing a parseable `## Bibliographic metadata` block, extract a minimal metadata block from the PDF's first page rather than skipping it entirely.

1. Run: `pdftotext -l 1 "<pdf-path>" -` to extract page-1 text. If `pdftotext` fails or returns empty (scanned/image PDF), fall back to: spawn a vision subagent on page 1 alone (converted via `pdftoppm -r 150 -l 1`) to OCR the title, authors, year, and venue.
2. From the extracted text, populate:
   ```
   doi: <if visible on page 1, else null>
   authors: [LastName1, LastName2, ...]
   title: <verbatim title>
   year: <year>
   venue: <journal/series/etc., verbatim>
   venue_type: journal | working_paper | book_chapter | other
   ```
3. Surface the extracted block to the user with the correct reason:
   - Bare PDF: "No `_text.md` found for `<stem>`. Extracted from page 1 — please verify before proceeding:"
   - Missing/malformed block: "`<stem>_text.md` is missing a parseable `## Bibliographic metadata` block. Extracted replacement metadata from page 1 — please verify before proceeding:"
   Then show the block.
4. Wait for confirmation (yes / edit / skip). On skip, exclude this stem from the run.
5. On confirmation, treat this block exactly as a parsed `_text.md` metadata block and enter the fetch cascade.

## Metadata block format

Each `_text.md` should begin with a `## Bibliographic metadata` block:

```
## Bibliographic metadata
doi: <10.xxxx/yyyy if present on the first page, else null>
authors: [LastName1, LastName2, ...]
title: <verbatim title from title page>
year: <year>
venue: <journal/working paper series/etc., verbatim>
venue_type: journal | working_paper | book_chapter | other
```

If a `_text.md` is missing this block entirely, or the block cannot be parsed, bootstrap from the matching PDF when available. If no matching PDF exists, warn and skip that paper — do not fail the run.

## Citation key

Use the filename stem verbatim (e.g., `Deryugina_etal_2019_AER`). If the fetched BibTeX entry has a different key, rewrite it to match the stem. If the stem's key already exists in `.bib` (in default mode), skip — never overwrite.

## Fetch cascade (per paper, stop at first success)

Run `scripts/fetch_bibtex.py` for each queued stem. The script encodes Sources 0–2 (DOI direct → CrossRef → OpenAlex), the 3-signal match test (title fuzzy ≥85%, year ±1, first-author match), three-way agreement against the parsed stem, and citation-key rewriting. Network errors, JSON parse errors, and empty content-negotiation bodies all fall through to the next source.

```bash
python3 ~/.claude/skills/bib-update/scripts/fetch_bibtex.py "<stem>" \
  --doi "<doi-or-empty>" \
  --first-author "<LastName>" \
  --title "<verbatim title>" \
  --year <year> \
  --venue "<venue>" \
  --venue-type <journal|working_paper|book_chapter|other>
```

The script prints a single JSON object to stdout:

```
{ "stem": "...", "tier": 1|2|3, "source": "doi-direct"|"crossref"|"openalex"|"fallback-needed",
  "bibtex": "@article{...}" | null,
  "match_signals": { "title_score": 0.94, "year_off_by_one": false, "author_ok": true } | null,
  "rejections": [{"source": "...", "candidate": "...", "reason": "..."}] }
```

### Result handling

- **Tier 1** (`source: doi-direct`): auto-append `bibtex`.
- **Tier 2** (`source: crossref` or `openalex`): auto-append `bibtex`; flag in the tier report. If `match_signals.year_off_by_one == true`, surface that in the report so the user can confirm the preprint-vs-published version is the intended one. **Preprint/published divergence override**: if the filename's venue (e.g., `_NBER`, `_SSRN`, `_IZA` indicates a working paper; standard journal abbrevs like `_AER`, `_QJE` indicate published) disagrees with the candidate's venue type implied by the returned BibTeX (`@techreport` vs `@article`), reject this result and treat as Tier 3.
- **Tier 3** (`source: fallback-needed`, `bibtex: null`): construct a BibTeX entry from the `_text.md` metadata block. Map `venue_type`:
  - `journal` → `@article`
  - `working_paper` → `@techreport` (institution = venue)
  - `book_chapter` → `@incollection`
  - `other` → `@misc`

  Mark this entry **unverified**. Block for per-entry user approval before appending.

## Review and append

Group results into three tiers and report to the user at the end of the run:

```
BibTeX update — N papers processed:

[auto-appended, no review needed]
✓ Deryugina_etal_2019_AER  — DOI direct (10.1257/aer.20161343)
✓ Card_Krueger_1994_AER    — CrossRef title-match (97%, year/author OK)

[auto-appended, flagged for spot-check]
⚠ Jones_2023_NBER           — CrossRef title-match (86%, year OK, author OK)

[REQUIRES APPROVAL — not yet appended]
? Wang_2021_WP              — LLM-from-metadata (unverified)
   @techreport{Wang_2021_WP,
     author      = {Wang, Yixin},
     title       = {The Effects of X on Y},
     year        = {2021},
     institution = {Working Paper},
   }
   Approve / Edit / Skip?
```

- **Tier 1** (DOI direct): auto-appended, no review.
- **Tier 2** (CrossRef or OpenAlex fuzzy match): auto-appended, flagged in the report for spot-check.
- **Tier 3** (LLM-from-metadata): printed in full, blocks for per-entry approval before appending.

## Update project CLAUDE.md pointer

After `references/references.bib` has been created or updated, ensure the project root `CLAUDE.md` points to it.

If `./CLAUDE.md` exists and does NOT already contain the literal string `references/references.bib`, add this pointer:

```markdown
- **Central BibTeX file**: `./references/references.bib` (maintained by `/bib-update`; cite from any `.tex` via `\bibliography{<relative-path>/references/references}`)
```

Placement:

1. If `CLAUDE.md` has a `## Key Files` section, insert the pointer into that section before the next `##` heading.
2. If there is no `## Key Files` section, append the pointer to the end of `CLAUDE.md`.
3. If `./CLAUDE.md` does not exist, skip silently.

This step is idempotent. Never add duplicate BibTeX pointers.

## Rules

- **Idempotent.** Re-running is always a safe no-op if all keys are present.
- **Never overwrite an existing entry** in default mode. `--rebuild-bib` is the only path to a full regeneration.
- **Never guess the DOI.** Use only what is in the metadata block or page-1 bootstrap. If `doi: null`, start at Source 1.
- **Filename stem is the citation key.** If the API returns a different key, rewrite it.
- **Missing metadata block → bootstrap if possible.** If a matching PDF exists, extract page-1 metadata and ask the user to verify it. If no matching PDF exists, warn and skip. Do not fail the entire run because one `_text.md` is missing or malformed.
- **Tier-3 entries block.** Never append an unverified LLM-constructed entry without explicit per-entry user approval.
- **Bootstrap requires confirmation.** Never enter the fetch cascade on a bootstrapped metadata block without user verification first.
