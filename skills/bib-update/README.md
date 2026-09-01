# bib-update

Assembles or refreshes `references/references.bib` from the `## Bibliographic metadata` blocks in each paper's `_text.md` extract. Those extracts can be created by `/split-pdf`, `/read-pdf`, or `/wiki-update`.

This is a maintenance companion to `/bibcheck`, not a replacement. `/bib-update` builds and refreshes the BibTeX file; `/bibcheck` audits an existing `.bib` for correctness.

## Usage

**Standalone** — run from a project root that has a `references/raw/` directory:

```
/bib-update
```

Scans all `*_text.md` files, skips papers already in `.bib`, and appends new entries. Safe to re-run at any time.

```
/bib-update --rebuild-bib
```

Confirms with you, then regenerates `.bib` from scratch for all papers. Blocks for per-entry approval on any entry that couldn't be verified via DOI or fuzzy title match.

**Automatic** — called as the final step of `/wiki-update`. You don't need to invoke it manually after a normal ingest run.

## Missing metadata or PDFs with no _text.md

If a PDF in `references/raw/` has no `_text.md` (e.g., it was added to the folder but never ingested), `/bib-update` will extract a minimal metadata block from page 1 via `pdftotext` (or a vision subagent for scanned PDFs), show it to you for verification, then proceed with the fetch cascade. This lets you add `.bib` entries for papers that don't need a full wiki ingest.

The same bootstrap path is used when a matching `_text.md` exists but is missing a parseable `## Bibliographic metadata` block. In that case `/bib-update` does not rewrite the extract; it uses verified page-1 metadata for the current BibTeX run.

## Citation key convention

The citation key for any paper is its filename stem, verbatim:

```
Deryugina_etal_2019_AER.pdf  →  @article{Deryugina_etal_2019_AER, ...}
```

This means the key you use in `.tex` files (`\cite{Deryugina_etal_2019_AER}`) always matches the filename in `references/raw/`.

## Fetch cascade

1. DOI direct (content-negotiation via `doi.org`) — definitive, no match test needed
2. CrossRef title+author search — 3-signal match test (year ±1, first-author, fuzzy title ≥85%)
3. OpenAlex title+author search — same match test
4. LLM-from-metadata fallback — blocks for your approval before appending

## Relationship to wiki-update

`/bib-update` reads the `## Bibliographic metadata` block that each per-paper subagent writes at the top of `_text.md`. It does not require a wiki, and it can bootstrap metadata from page 1 when a PDF has no `_text.md` or the extract is missing its metadata block.

After creating or updating `references/references.bib`, `/bib-update` also idempotently adds a pointer to the project root `CLAUDE.md` if one is not already present. It inserts the pointer under `## Key Files` when that section exists, or appends the pointer to the end otherwise.
