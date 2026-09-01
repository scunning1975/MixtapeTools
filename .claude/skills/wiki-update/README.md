# Wiki-Update (`/wiki-update`)

> **Ingest new PDFs from a project's `references/raw/` into the project's wiki — relevance-filtered, atomically per paper, with BibTeX maintenance handed to `/bib-update`.**

`/wiki-update` is the maintenance skill for the project wiki created by `/newproject`. You drop new papers into `references/raw/`, invoke the skill, and it discovers them, summarizes them through the lens of your project's research focus, writes new wiki pages, updates existing pages with cross-references, and then calls `/bib-update` to refresh the central BibTeX file — all without re-reading papers it has already processed.

## When to use it

After adding one or more PDFs to `references/raw/`. Triggers include:
- "ingest new references"
- "update the wiki"
- "process the new papers I added"

The skill is also designed to be safe to re-invoke: if a previous run failed mid-way, the next invocation rediscovers the unprocessed papers and retries from scratch.

## Prerequisites

**This skill expects** (or creates on first invocation):

- `references/raw/` (PDFs land here)
- `references/wiki/` (concept pages and the running log)
- `references/CLAUDE.md` (project-specific wiki conventions)
- A filled-in project root `CLAUDE.md` with research question, data sources, and identification strategy

**First-run note.** If `references/raw/` does not exist when you invoke this skill, it will be created automatically along with the rest of the wiki structure (`references/wiki/`, `references/CLAUDE.md`, `wiki/index.md`, `wiki/log.md`). Just put PDFs in `references/raw/` for the next invocation to ingest.

The project root `CLAUDE.md` is *not* auto-created — if it's missing or its placeholders are unfilled, `/wiki-update` stops and asks you to fill in the project context first. It will not guess the research question.

## What it does

```
/wiki-update                              # ingest all new PDFs
/wiki-update "focus on IV strategies"     # additional batch focus
```

The skill works in three phases:

### 1. Pre-flight (main session)

- Verifies the project structure exists
- Reads `references/CLAUDE.md` for project-specific format conventions
- Reads `references/wiki/log.md` to find previously-ingested filenames
- Lists new PDFs and proposes filename normalizations (per the convention `Last_Year_Venue.pdf` / `Last1_etal_Year_Venue.pdf`)
- Presents proposed renames in a single batch for one approve/edit/reject decision

### 2. Per-paper ingest (subagents)

For each new paper, a subagent runs in isolation (so PDF page images don't bloat the main conversation context). The subagent:

- Picks the right ingest protocol:
  - **Protocol M** — use `/read-pdf`'s marker conversion cache when available
  - **Protocol E** — use an existing `<basename>_text.md` extract directly
  - **Protocol S** — split the PDF into 4-page chunks and read the splits without the interactive `/split-pdf` confirmation gate
- Extracts content along the 11 dimensions defined by the skill, including tables and figures
- Applies the **relevance filter**: sections directly relevant to the project's research focus get full treatment in the wiki; less-relevant sections get a one-liner with a page reference. Nothing is fully omitted.
- Writes new concept pages and appends to existing pages directly
- Returns proposed *destructive* edits (rewording existing claims, deleting lines, modifying summaries) to the main session as diffs for user approval

### 3. Per-paper atomicity (main session)

For each paper:
- Apply approved destructive edits
- Append a single line to `wiki/log.md` *only after* all wiki edits succeed
- If anything fails before the log write, the next invocation will rediscover the paper as new and retry

### 4. BibTeX handoff (main session)

After all papers are ingested, call `/bib-update` in append-only mode. `/bib-update` reads the `## Bibliographic metadata` blocks from `_text.md` extracts, skips citation keys already present in `references/references.bib`, and handles DOI/CrossRef/OpenAlex/fallback entry generation.

## Key features

### Three-tier reuse

The skill never re-reads a paper it has already processed. Cached `_text.md` extracts and existing splits are detected automatically and reused. A second invocation on the same papers is essentially free.

### Subagent isolation

Long PDFs render as image data that accumulates permanently in conversation context. Two or three large papers in the main session can crash the conversation. By delegating all PDF reading to subagents, the main session's context stays bounded — the main session only ever reads plain markdown returned by the subagents.

### Atomic per-paper writes

Each paper either fully succeeds at the wiki layer (all wiki edits + log entry) or fully fails with no log entry. If a run fails after the rollback journal is built, created/modified wiki pages are restored before retry. Converter caches, split `notes.md`, and `_text.md` extracts are treated as reusable intermediate artifacts, not part of the wiki rollback journal.

### Project-context-driven relevance filtering

The wiki is not a neutral summary archive — it's a focused map of the literature relevant to *this* project. The skill reads the project's research question and identification strategy from `CLAUDE.md` and uses that to decide what gets full treatment vs. a one-liner. The optional batch focus argument supplements this for unusual cases.

### BibTeX handoff

The wiki ingest step writes the metadata that `/bib-update` needs, then delegates BibTeX maintenance to that skill. Keeping the fetch cascade in `/bib-update` avoids duplicating bibliography rules here.

## Hard rules

- **Never modifies source PDFs without approval** — canonical renames require the batched approval flow
- **Never reads PDF extracts in the main session** — always delegated to subagents
- **Never writes the log entry before wiki edits complete** — the log lags, never leads
- **Never invents project context** — if `CLAUDE.md` placeholders are unfilled, stops and asks
- **Never renames a PDF without user approval** — even a single non-conforming file goes through the batched propose/approve flow

## Files in this skill

- [`SKILL.md`](SKILL.md) — the full operational protocol (pre-flight, per-paper subagent prompt, BibTeX handoff, error handling)

## Related skills

- **`/newproject`** — creates the directory structure that `/wiki-update` assumes. If you haven't scaffolded a project with `/newproject`, this skill will fail pre-flight.
- **`/read-pdf`** — preferred Protocol M converter for layout-aware markdown, tables, figures, and equations.
- **`/split-pdf`** — the underlying batched-reading method. `/wiki-update` inlines the splitting logic rather than invoking `/split-pdf` directly, because `/split-pdf` has a per-batch user-confirmation gate that would deadlock inside a subagent.
- **`/bib-update`** — maintains `references/references.bib` from the metadata blocks written during ingest.

## Acknowledgments

The conceptual foundation for this skill — maintaining a project-specific LLM-readable wiki that grows alongside the research and is consumed by future LLM sessions as compressed institutional memory — is owed to [Andrej Karpathy's LLMwiki concept](https://x.com/karpathy). `/wiki-update` operationalizes that idea for empirical-economics workflows: relevance-gated ingestion of new papers into a structured wiki that the project's `CLAUDE.md` indexes.
