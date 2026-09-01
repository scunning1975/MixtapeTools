# `/wiki-update` — Reference wiki ingest

**Skill location:** [`.claude/skills/wiki-update/SKILL.md`](../../.claude/skills/wiki-update/SKILL.md)

---

## What This Skill Does

You drop one or more PDFs into a project's `references/raw/` folder, run `/wiki-update`, and the skill ingests each paper into a structured wiki at `references/wiki/`. For each paper it:

1. **Auto-detects the best ingest path** (see below) and produces a structured 11-dimension extract (`<basename>_text.md`) with a 200-word plain-English synthesis at the top.
2. **Updates the wiki:** creates new concept pages, appends to existing ones, embeds or references figures, and adds backlinks. Destructive edits to existing pages are returned as diffs for user approval rather than applied silently.
3. **Atomically logs** the ingest in `wiki/log.md` only after wiki edits succeed — failed runs leave nothing partially committed.
4. **Assembles BibTeX entries** for each ingested paper via a DOI → CrossRef → OpenAlex → LLM-fallback cascade, appended to `references/references.bib`.

The wiki is shaped by per-project conventions in `references/CLAUDE.md`, which the skill reads first and treats as authoritative.

---

## Auto-Detection: Three Ingest Paths

The skill picks the best available path per paper, in order:

| Protocol | Condition | What it does |
|---|---|---|
| **M — Converted markdown** | `read-pdf`'s converter is installed | Runs `convert.py` (or uses its cache) → high-fidelity markdown with tables, figures, equations |
| **E — Cached extract** | `_text.md` already exists | Reads the existing structured extract and writes wiki pages directly |
| **S — Split-PDF pipeline** | Neither above | Splits PDF into 4-page chunks, reads in batches with vision, synthesizes `_text.md` |

**Protocol M** is the richest path: the marker layout-aware converter produces pipe-syntax tables ready for copy-paste, pixel-accurate figure PNGs that are copied directly into `references/wiki/figures/`, and verbatim LaTeX equations. It requires a one-time venv install (~500 MB, 1–3 min, handled lazily by `/read-pdf`). After that, conversions are cached by content hash — re-ingesting the same PDF is free.

**Protocol S** is the zero-install fallback. Tables and figures are still captured — tables via careful reading of the PDF splits, figures via CLIP placeholders that you fill in by manually clipping from the PDF. It costs more tokens than Protocol M.

The skill reports which tier each paper was assigned before spawning any subagents.

`pdftotext` is not a substantive ingest path. It may be used for narrow pre-flight checks such as first-page filename proposals when the converter is unavailable or metadata/bootstrap checks, but Protocol M must read from converted `markdown.md`, and Protocol E must read from the cached `_text.md`.

---

## Layout

```
project-root/
├── CLAUDE.md                          # research question, data, identification (must be filled in)
└── references/
    ├── CLAUDE.md                      # wiki conventions (rendered from skill template on first run)
    ├── references.bib                 # BibTeX entries (appended by this skill)
    ├── raw/                           # immutable source PDFs + per-paper structured extracts
    │   ├── Smith_2024_AER.pdf
    │   ├── Smith_2024_AER_text.md     # written by this skill — reusable cross-session
    │   └── raw_build/                 # splits cache for Protocol S (never modify)
    │       └── split_Smith_2024_AER/
    └── wiki/
        ├── index.md                   # table of contents — appended on each ingest
        ├── log.md                     # append-only ingest log
        ├── figures/                   # figure clips (Protocol M copies; Protocol S uses placeholders)
        │   └── Smith_2024_AER_fig3.png
        └── <concept-pages>.md         # one per concept; updated by ingest, linked via [[wiki-links]]
```

---

## Usage

```
/wiki-update
/wiki-update "focus on IV strategies and instrument validity"
/wiki-update --rebuild-bib
```

The optional focus string applies to this batch in addition to the project's standing context (research question, data, identification strategy, read from `./CLAUDE.md`).

`--rebuild-bib` re-runs the BibTeX fetch cascade for all previously-ingested papers using cached `_text.md` metadata — useful for repairing or updating `references.bib` without re-reading any PDFs.

---

## What Gets Extracted (11 Dimensions)

For each paper, the structured extract covers:

1. Research question
2. Audience
3. Method / identification strategy
4. **Target parameter** — the estimand in plain terms (distinct from method and identification assumptions)
5. Data — sources, unit of observation, sample size, time period
6. Statistical methods / specifications — including **key equations verbatim** in LaTeX (Protocol M extracts them from the converter; Protocol S reads them from the PDF text)
7. Findings — key coefficients and standard errors
8. Contributions
9. Replication feasibility
10. **Tables** — pipe-syntax markdown, project-relevant tables only (Protocol M gets these from the converter output; Protocol S reads them from splits)
11. **Figures** — Tier A (data figures: structured optical description + image embed for M, structured description for S) or Tier B (schematics: image embed for M, CLIP placeholder for S)

Plus a `Bibliographic metadata` block at the top (DOI, authors, title, year, venue, venue_type) for the BibTeX step.

---

## Pre-Flight Checks

- **Lazy scaffolding** — creates `references/raw/`, `references/wiki/`, `references/wiki/figures/`, `references/CLAUDE.md`, `wiki/index.md`, `wiki/log.md` on first invocation. Idempotent on re-runs.
- **Project context check** — refuses to proceed if `./CLAUDE.md` has unfilled placeholder fields. Relevance filtering depends on the research question, data sources, and identification strategy.
- **Non-PDF surfacing** — any non-PDF files in `raw/` are reported to the user before ingest starts.
- **Filename normalization** — proposes `Last_Year_Venue.pdf`-style renames for non-conforming PDFs and asks for batched approval before applying `mv`.
- **Tier classification** — runs per-paper detection (converter cache check → `_text.md` check → splits check) and reports the tier breakdown before spawning any subagents.

---

## Per-Paper Subagent Isolation

Each paper is ingested by a dedicated subagent so that converted markdown and extracted figures don't accumulate in the main session's context across papers. The main session orchestrates: spawning subagents, surfacing user-approval prompts, journal-and-rollback on failure, and writing the log entry only after wiki edits succeed.

---

## What This Skill Does NOT Do

- **No PDF download.** Drop them into `references/raw/` first.
- **No silent converter fallback.** If `convert.py` errors on a specific paper, the skill reports the error and falls through to Protocol E or S for that paper rather than substituting `pdftotext` output silently.
- **No `pdftotext` summaries.** Once a paper is assigned to Protocol M or E, `pdftotext` must not be used to read, summarize, validate, or supplement the paper's substantive content.

---

## Acknowledgments

Inspired by Andrej Karpathy's [LLM Wiki](https://karpathy.bearblog.dev/llm-wiki/) pattern — a structured, interlinked knowledge base maintained by an LLM, curated by a human. The Tier A / Tier B figure protocol, the project-relevance gate, and the substantive-change rule are workflow refinements specific to academic-paper ingest at scale.

The local-conversion path (Protocol M) relies on [marker](https://github.com/VikParuchuri/marker), an open-source layout-aware PDF parser whose authors did the actual hard work.

This skill originated in [Scott Cunningham](https://github.com/scunning1975/MixtapeTools)'s MixtapeTools repository.
