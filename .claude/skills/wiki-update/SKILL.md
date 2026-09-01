---
name: wiki-update
description: >-
  Ingest new PDFs from a project's references/raw/ folder into the project's wiki,
  following the project's wiki conventions and filtering for relevance to the
  project's research focus. Auto-detects the best ingest path: converted markdown
  (via read-pdf's converter, if installed) for high-fidelity tables, figures, and
  equations; cached structured extract (_text.md) if available; or full split-PDF
  pipeline as fallback. Creates `references/raw/`, `references/wiki/`, and
  `references/CLAUDE.md` on first invocation if absent. Calls `/bib-update`
  automatically at the end to refresh `references/references.bib`. Use when the
  user adds new papers to references/raw/ and asks to update the wiki, or says
  "ingest new references", "update the wiki", or similar.
allowed-tools: Read, Edit, Write, Glob, Grep, Bash(ls*), Bash(pdftotext:*), Bash(python3:*), Bash(mv:*), Bash(cp:*), Bash(mkdir:*), Bash(touch:*), Agent
argument-hint: [optional focus or theme for this batch]
---

# wiki-update: Ingest new references into the project wiki

Maintains a project's reference wiki by ingesting newly-added PDFs from `references/raw/`, summarizing each through the lens of the project's research focus, and updating the wiki atomically per-paper.

**Ingest path is auto-detected per paper.** If the read-pdf converter is installed, it runs first for high-fidelity markdown (Protocol M: best tables, figures, and equation handling). If only a cached `_text.md` extract exists, that feeds wiki writing directly (Protocol E). Otherwise the full split-PDF vision pipeline runs (Protocol S). All three paths produce the same wiki output — the difference is quality of table and figure capture.

**`pdftotext` is not an ingest source.** It is allowed only for narrow pre-flight tasks: first-page filename proposals when the converter is unavailable, metadata checks needed for `/bib-update`, and other explicit bootstrap/diagnostic checks that do not synthesize wiki content. Once a paper is assigned to Protocol M or Protocol E, do not use `pdftotext` to read, summarize, validate, or supplement substantive content. Wait for the selected input (`markdown.md` or `_text.md`) and read that source only.

## When this skill is invoked

The user has added one or more PDFs to `references/raw/` and wants the wiki updated. The optional argument is a free-form focus string (e.g., "focus on IV strategies and instrument validity") that applies to this batch in addition to the project's standing context.

## Pre-flight (main session)

Run all checks before any ingest work. If anything fails, stop and ask the user.

### 0. Lazy scaffolding (first invocation in a project)

Before the other pre-flight checks, self-bootstrap the wiki structure if it's absent. All steps are idempotent — re-invocations against an already-scaffolded project are no-ops.

**a. Check for `references/`.** If `./references/` does not exist:

1. Create the directory tree:
   ```bash
   mkdir -p references/raw references/wiki references/wiki/figures
   ```
2. Render `references/CLAUDE.md` from the template at `~/.claude/skills/wiki-update/templates/references_CLAUDE.md`, substituting `{{PROJECT_NAME}}` with the current project's name (use the basename of the project root — typically the current working directory).
3. Initialize `references/wiki/index.md`:
   ```markdown
   # Wiki Index — [project-name]

   | Page | Description |
   |------|-------------|
   ```
4. Initialize `references/wiki/log.md`:
   ```markdown
   # Wiki Log — [project-name]

   | Date | Source | Changes |
   |------|--------|---------|
   ```

If `./references/` already exists, skip. Do not clobber any existing files.

**b. Append a wiki-references entry to the project's root `CLAUDE.md` (idempotent).** If `./CLAUDE.md` exists at the project root and does NOT already contain a reference to `references/CLAUDE.md` (grep for the literal string `references/CLAUDE.md`), append:

```markdown
- See `references/CLAUDE.md` for wiki conventions and the project's reference library.
```

If `./CLAUDE.md` does not exist, skip silently.

After this self-bootstrap, the rest of the pre-flight (steps 1–6 below) runs as before.

### 1. Locate the wiki

Check that `./references/raw/` and `./references/wiki/` both exist relative to the current working directory. If either is still missing after the lazy-scaffolding step, ask the user where the wiki lives. Do not search parent directories.

Read `./references/CLAUDE.md` for project-specific wiki conventions (page format, citation rules, naming). These conventions take precedence over anything in this skill if they conflict — this skill defines *workflow*, not *format*.

### 2. Verify project context is filled in

Read `./CLAUDE.md` (the project root file). Check the "Research Question," "Data Sources," and "Identification Strategy" fields (or their equivalents). If any are still placeholder text — bracketed phrases like `[What are you trying to answer?]`, `[What data are you using?]`, or otherwise unfilled — **stop and ask the user to fill them in first**. Explain that relevance filtering depends on this context.

The optional `[focus]` argument supplements but does not replace the project CLAUDE.md context.

### 3. Discover new papers

Read `./references/wiki/log.md` to find previously-ingested filenames. List files in `./references/raw/` that do not appear in the log.

**Non-PDF files:** If any non-PDF files are present in `raw/`, surface them before continuing:

```
Non-PDF files found in references/raw/: <filenames>
These were skipped for ingest. Move them elsewhere if they don't belong, or tell me if any should be treated differently.
```

Include skipped filenames in the end-of-run summary under "Skipped (non-PDF)."

Proceed with PDF files only, in filename-sorted order. If no new PDFs are found, report that and exit.

### 4. Normalize filenames

Each new PDF must conform to the project naming convention before ingest. This runs in the **main session** (not subagents) so renames can be batched and approved once.

**Convention:**
- 1 author → `Last_Year_Venue.pdf`
- 2 authors → `Last1_Last2_Year_Venue.pdf`
- 3+ authors → `Last1_etal_Year_Venue.pdf`
- Venue slug: standard econ journal abbreviation (`AER`, `JPE`, `QJE`, `JEEM`, `JHE`); `NBER` / `SSRN` / `IZA` for known WP series; `WP` for generic working papers; chapter abbrev or `Book` for book chapters.

**Skip condition.** A filename matching
```
^[A-Z][a-zA-Z]+(_[A-Z][a-zA-Z]+|_etal)?(_[A-Z][a-zA-Z]+){0,2}_\d{4}_[A-Z][A-Za-z]+\.pdf$
```
is already-conforming and passed through untouched. Non-conforming files go through the propose-and-approve flow below.

**Extracting text for name proposal:**

For each non-conforming file, extract enough text to propose a name. Choose the method based on what's available:

- **If `~/.claude/skills/read-pdf/convert.py` exists:** run
  ```bash
  python3 ~/.claude/skills/read-pdf/convert.py "<pdf-path>"
  ```
  Capture the printed path to `markdown.md`. Read the first ~2000 characters of `markdown.md` — this covers title, authors, year, and venue. This also primes the converter cache for the ingest step that follows (the cache is SHA-keyed, so renaming the PDF after this point does not invalidate it).

- **Otherwise:** run `pdftotext -l 1 "<pdf-path>" -` and read the output.

If either method returns empty or <50 chars of non-whitespace, mark the file as **unparseable** and flag for manual handling.

This `pdftotext` fallback is for filename proposal only. Do not reuse its output for paper synthesis, wiki page writing, tables, figures, or relevance filtering.

**Batched approval.** After proposals for all non-conforming files are ready, present as one block:

```
Proposed renames (N files):
  <current-name>  → <proposed-name>
  ...

Already conform (skipped): K files

Unparseable (needs manual decision):
  ⚠ <current-name>  — extraction failed: <reason>
    Keep as-is / Provide name?

Approve all / Edit (per-file) / Reject all?
```

- **Approve all** → apply all renames via `mv`.
- **Edit** → per-file review; for each, user can approve, edit, or skip.
- **Reject all** → proceed with no renames.

**Collision handling** (before any `mv`): proposed name matches existing file → block and ask user to provide an alternative. Two proposals in the batch collide with each other → flag both, require disambiguation (e.g., appending a title word).

Never silently overwrite. Never proceed past a collision without user input.

After renames are applied, re-list new PDFs under their new names before continuing.

### 5. Pre-scan: classify each paper into an ingest tier

For each new paper (using its post-rename canonical name), determine its ingest protocol. This classification runs entirely in the main session — each subagent receives exactly one protocol with no branching.

**Check order (stop at the first match):**

1. **Tier M — Converted markdown:** `~/.claude/skills/read-pdf/convert.py` exists, **and** running it for this PDF succeeds (cache hit is instant; a miss triggers the full conversion here). Capture the returned `markdown.md` path and cache directory. If `convert.py` was already run during step 4 for this paper, it was cached — re-running is a no-op.

   If `convert.py` exists but fails for a specific paper (conversion error), report the error, skip tier M for that paper, and fall through to tier E or S. Do not use `pdftotext` as a temporary or parallel substitute while conversion is running or after conversion fails.

2. **Tier E — Cached extract:** `references/raw/<basename>_text.md` exists. No conversion needed.

3. **Tier S — Split-PDF pipeline:** Neither of the above. Check whether `references/raw/raw_build/split_<basename>/` already exists (splits cached from a prior interrupted run) — pass this as `splits_exist=true|false` to the subagent.

**Report tier breakdown once, before spawning subagents:**

```
Ingest tiers for this batch:
  M (converted markdown): N papers
  E (cached extract):     M papers
  S (full pipeline):      K papers  [X with cached splits]

[If any converter failures:]
  ⚠ Converter failed for: <filenames> — falling back to E or S
```

### 6. Read the wiki index

Load `./references/wiki/index.md` once. Pass it into each per-paper subagent so it can match new concepts against existing pages and avoid creating duplicates.

---

## Per-paper ingest (subagent)

Spawn one Agent per paper, sequentially. The main session must not read PDF extracts or markdown directly — delegate deep reading to subagents to bound context.

Each subagent prompt must be self-contained — the agent has no memory of this conversation. Include:

- Absolute paths: PDF, input source (markdown.md, `_text.md`, or PDF/splits), `references/raw/`, `references/wiki/`, `references/wiki/figures/`, `references/CLAUDE.md`
- The tier (M, E, or S) and `splits_exist` flag if tier S
- Current `wiki/index.md` contents (for disambiguation)
- Project context block: research question, data sources, identification strategy (from `./CLAUDE.md`)
- Optional batch focus string (if provided as the skill argument)
- The verbatim protocol for this tier (M, E, or S — from the sections below)
- The common verbatim sections: structured-extraction dimensions, tables protocol, figures protocol variant for this tier, substantive-change rule, concept page disambiguation, relevance filtering, subagent return value

---

### Protocol M — Converted Markdown

*Input:* path to `markdown.md` (in the converter cache), path to the cache directory (for figures), canonical paper basename.

Protocol M reads only the converted `markdown.md`, `meta.json`, and cache-local figure/equation files. Do not inspect the source PDF with `pdftotext` or any other text extractor for substantive synthesis, even if conversion is slow. If conversion is still running, wait.

**Step 1: Check for equation fallback.**

Read `<cache-dir>/meta.json`. If `equation_extraction_mode == "image_fallback"`, equations were extracted as `<cache-dir>/figures/eq_*.png` rather than inline LaTeX. Before synthesis, transcribe each:

```
Read the image at <eq-png-path>. It is a single equation clipped from an academic paper.
Transcribe it as LaTeX, in display math mode ($$ ... $$). Output only the LaTeX —
no commentary, no surrounding text. If the equation is not legible, output "[unreadable equation]".
```

Edit `<cache-dir>/markdown.md` in place to replace each `![](figures/eq_N.png)` with the transcribed LaTeX. (The cache markdown is scratch — overwriting is fine; `convert.py` regenerates it on a hash miss.)

**Step 2: Synthesize `_text.md`.**

Read `markdown.md`. Produce `references/raw/<basename>_text.md` following the `_text.md` structure below (bib block, plain-English synthesis, 11 structured dimensions). Write or overwrite if a prior partial file exists.

For the bib metadata block: scan `markdown.md` for the DOI regex `10\.\d{4,}/\S+`. Extract authors, title, year, and venue from the title page text. Record null for any field not found.

**Step 3: Copy and classify relevant figures.**

For each figure in `markdown.md` (referenced as `![](figures/fig_N.png)`):
1. Identify the paper figure number from surrounding caption text.
2. Apply the project-relevance filter. Non-relevant: one-line description + page ref only; do not copy.
3. For relevant figures:
   - Copy from cache to wiki: `cp <cache-dir>/figures/fig_N.png references/wiki/figures/<basename>_fig<M>.png` (where M is the paper's figure number). Before the first copy, run `mkdir -p references/wiki/figures` (idempotent).
   - Classify as Tier A (data figure: scatter, line, bar, coefplot, histogram, density, time series, RD/event-study plot) or Tier B (schematic: DAG, conceptual diagram, map, flowchart, theoretical model). Use the caption text; read the PNG only if the caption is genuinely ambiguous.

**Step 4: Write wiki pages** using the substantive-change rule and relevance filtering below.

For relevant figures embedded in wiki concept pages, use this format regardless of Tier A/B:

```markdown
**Figure N:** <verbatim caption> (p. 12)

![<short description>](../figures/<basename>_figN.png)

- Key visual finding: <one sentence — what the eye sees / the point of the figure>
- **Figure notes:** <verbatim notes printed below the figure in the paper, if any>
```

The Tier A/B distinction lives in `_text.md` only (full optical decomposition for Tier A; schematic one-liner for Tier B). Wiki pages use the same lightweight embed format for all figures.

**Return value additions for Protocol M:**

```
Figures copied: [list of {source_cache_path, dest_wiki_path, paper_figure_label}]
Equation fallback used: <true/false> (with count and any "[unreadable equation]" instances if true)
```

---

### Protocol E — Cached Extract

*Input:* path to `references/raw/<basename>_text.md`.

**Step 1: Read the extract.**

Read `_text.md` in full. Extract the `## Bibliographic metadata` block for the return value. Note any CLIP placeholders in the figures sections (these were created by a prior Protocol S run and are still pending).

Protocol E reads only the cached `_text.md` and any figure files it references. Do not re-read the PDF with `pdftotext` to expand or validate the extract.

**Step 2: Write wiki pages** using the substantive-change rule and relevance filtering below.

For figures: if `_text.md` references wiki figure paths that already exist on disk (from a prior Protocol M run), embed them in wiki pages using the same lightweight format as Protocol M. If `_text.md` contains CLIP placeholders, pass them through to the wiki and aggregate them into the Pending CLIPs return field.

Do **not** re-synthesize or overwrite `_text.md` — it is the canonical extract for this paper.

**Return value additions for Protocol E:**

```
Pending CLIPs: [list of {target_path, source_paper, page_number, one_liner} — forwarded from _text.md]
```

---

### Protocol S — Split-PDF Pipeline

*Input:* absolute path to the PDF, absolute path to the splits directory (`references/raw/raw_build/split_<basename>/`), `splits_exist` boolean.

**Step 1: Split (if needed).**

If `splits_exist=false`: split the PDF into 4-page chunks using PyPDF2, writing to `<splits-dir>/`. The canonical splits directory is `references/raw/raw_build/split_<basename>/` — use this exact path. Do not derive it yourself.

**Step 2: Read splits in batches of 3.**

Read each split sequentially in batches of 3, without pausing or asking for confirmation. After each batch, append findings to `<splits-dir>/notes.md` under the structured-extraction dimensions below, preceded by a batch boundary comment:

```
<!-- batch N: pp X-Y -->
```

If `notes.md` already exists (prior interrupted run), read it first and resume from where it left off — do not overwrite earlier content. `notes.md` is append-mostly and permanent; never delete it.

**Step 3: Synthesize `_text.md`.**

After all splits are read, write `references/raw/<basename>_text.md` from the accumulated `notes.md` content. Follow the `_text.md` structure below (bib block, plain-English synthesis, 11 dimensions).

For the bib metadata block: scan the first split for the DOI regex `10\.\d{4,}/\S+`. Extract authors, title, year, and venue from the first-split text. Record null for any field not found.

`notes.md` is permanent — do not delete it after writing `_text.md`.

**Step 4: Write wiki pages** using the substantive-change rule and relevance filtering below.

For figures: Protocol S does not have extracted figure images. Use CLIP placeholders for all Tier B figures and for any Tier A data figures that cannot be adequately described in text. A structured Tier A block suffices when the data description is complete; use a CLIP placeholder when it isn't.

CLIP placeholder format in `_text.md`:

```
> **Figure N (CLIP):** <verbatim caption> (p. 12)
> One-liner: <what the figure depicts at a glance>
> ACTION: clip from PDF, save to references/wiki/figures/<basename>_fig<N>.png
```

When a wiki page references a CLIP figure, use a broken image link (it renders as a visible TODO):

```markdown
![<short description>](../figures/<basename>_figN.png)
*<verbatim caption> ([<basename>](../log.md), p. 12)*
```

Before writing any CLIP placeholder that references the figures directory, ensure it exists: `mkdir -p references/wiki/figures`.

**Return value additions for Protocol S:**

```
Pending CLIPs: [list of {target_path, source_paper, page_number, one_liner}]
```

---

### Common: `_text.md` structure

All protocols that synthesize `_text.md` (M and S) use this layout:

```markdown
## Bibliographic metadata
doi: <10.xxxx/yyyy if found, else null>
authors: [LastName1, LastName2, ...]
title: <verbatim title>
year: <year>
venue: <journal/WP series/etc., verbatim>
venue_type: journal | working_paper | book_chapter | other

## Plain-English synthesis
[~200 words, see below]

## 1. Research question
...
## 2. Audience
...
[continue through dimension 11]
```

### Common: Plain-English synthesis block

Hard cap: ~200 words. No jargon. Cover:

- Research question (1 sentence)
- Motivation / why it matters (1–2 sentences)
- What they estimate and how, in plain terms (2–3 sentences)
- What they found (1–2 sentences)
- The take-away — what someone should walk away believing or doing differently (1 sentence)

This block is the answer to "what's this paper about?" for someone who will not read the rest. Anyone with a college degree should be able to read it without a glossary. If you find yourself writing "endogeneity" or "LATE" or "first-stage F-stat," rewrite in plainer terms.

### Common: Structured-extraction dimensions

1. **Research question** — what the paper asks and why it matters
2. **Audience** — sub-community of researchers who care
3. **Method / identification strategy** — how they answer the question
4. **Target parameter** — the estimand in plain terms (e.g., "ATE of schooling on log wages, conditional on age and state-by-year FE"). Distinct from method and identification assumptions.
5. **Data** — sources, unit of observation, sample size, time period
6. **Statistical methods / specifications** — econometric techniques, key specifications, key equations (extract verbatim in LaTeX math mode where available — Protocol M gets these from the converter; Protocol S extracts them from split text)
7. **Findings** — key coefficients and standard errors
8. **Contributions** — what is learned that we didn't know before
9. **Replication feasibility** — data availability, replication archive
10. **Tables (project-relevance gated)** — see Tables protocol below
11. **Figures (project-relevance gated)** — see Figures protocol below

### Common: Tables protocol (project-relevance gated)

Apply the project-relevance filter. For tables *directly relevant* to the project's research focus, extract in machine-readable markdown. For non-relevant tables, one-line description with page reference.

For relevant tables:

```
**Table N:** <verbatim caption> (p. 12)

| Variable | (1) | (2) | (3) |
|---|---|---|---|
| Schooling | 0.087*** | 0.091*** | 0.085*** |
|           | (0.012)  | (0.013)  | (0.011)  |
| N         | 12,450   | 12,450   | 12,450   |
| R²        | 0.34     | 0.36     | 0.38     |

Notes: <verbatim table notes — SE clustering, FE structure, etc.>
```

Preserve column headers verbatim, numerical values verbatim (including SEs in parentheses and significance stars), and table notes verbatim. Pipe-syntax markdown only; no HTML tables. Table notes are part of the table's content — capture them.

*Protocol M advantage:* the converter already produces pipe-syntax tables from the PDF. Extract them with light cleanup rather than re-reading the figures.

### Common: Figures protocol (project-relevance gated, two-tier)

Apply the project-relevance filter. Non-relevant figures: one-line description with page reference only.

For relevant figures, classify as Tier A or Tier B using caption text:

- **Tier A — Data figures**: scatter, line, bar, coefplot, histogram, density, time series, RD/event-study plot. The data IS the content.
- **Tier B — Schematic figures**: DAGs, conceptual diagrams, maps, flowcharts, theoretical model schematics. Do NOT attempt optical decomposition. Default to Tier B when uncertain — a structured Tier A block written for a schematic is misleading; a Tier B for a data figure just makes the reader look at the image.

**In `_text.md`:**

*Protocol M* — figures are copied to `references/wiki/figures/`. Record:

```
**Figure N:** <verbatim caption> (p. 12)
![<short description>](../wiki/figures/<basename>_figN.png)
- Type: <for Tier A: scatter / line / bar / etc.>
- X-axis: <variable, units, range>    [Tier A only]
- Y-axis: <variable, units, range>    [Tier A only]
- Series / panels: <brief list>       [Tier A only]
- Key visual finding: <one sentence>
- Annotations: <labels, reference lines, shaded regions>  [Tier A only]
- **Figure notes:** <verbatim notes below the figure, if any>
[Tier B: replace the structured block with just: One-liner: <what the figure depicts at a glance>]
```

*Protocols E and S* — use CLIP placeholders (described in their respective protocol sections).

### Common: Substantive-change rule (passed to subagent verbatim)

The subagent applies non-destructive edits directly. Destructive edits to existing pages must be returned as proposed unified diffs — not applied.

| Edit | Apply directly? |
|---|---|
| Create new wiki page | Yes |
| Append new section / bullet / paragraph to existing page | Yes |
| Add `[[backlink]]` (inline or under "Related pages") | Yes |
| Update `**Last updated**` date | Yes |
| Append a new source to `**Sources**` | Yes |
| Note a contradiction between sources (additive note) | Yes |
| Reorganize section order (no content lost) | Yes |
| Update `wiki/index.md` (append new entries, edit existing one-liners) | Yes |
| Copy an extracted figure into `references/wiki/figures/` | Yes |
| Edit the `**Summary**` field on an existing page | **Return as diff** |
| Delete any existing line | **Return as diff** |
| Modify the wording of an existing claim | **Return as diff** |

### Common: Concept page disambiguation (subagent)

Before creating a new concept page, check `wiki/index.md` for existing pages covering the same concept — including obvious synonyms (e.g., "RDD" vs "regression discontinuity"). If a near-match exists but you aren't confident, do **not** create a new page; return the ambiguity to the main session as a question for the user.

### Common: Relevance filtering (subagent)

Apply "compress, don't omit": sections directly relevant to the project's research focus get full treatment. Less-relevant sections get a one-line description plus page reference. Nothing is fully omitted.

### Common: Subagent return value

```
Pages created: [list]
Pages modified non-destructively: [list with brief description]
Proposed destructive edits: [list of {page, unified diff, rationale}]
Disambiguation questions: [list of {concept, candidate existing pages}]
Proposed log entry: [single line for wiki/log.md]
Pending CLIPs: [list of {target_path, source_paper, page_number, one_liner}]
[Protocol M only] Figures copied: [list of {source_cache_path, dest_wiki_path, paper_figure_label}]
[Protocol M only] Equation fallback used: <true/false>
Errors: [any issues encountered]
```

---

## Per-paper atomicity (main session)

For each paper, the main session uses a **journal-and-rollback** pattern to guarantee the wiki is never left in an inconsistent state.

**Execute the write sequence:**
1. Spawn the subagent and wait for its return summary.
2. If there are disambiguation questions, ask the user; pass answers back via a follow-up SendMessage to the same agent (or apply decisions directly if simple).
3. Build the rollback journal from the returned page lists and proposed diffs: for every wiki page that will be created, note that it does not exist; for every wiki page that will be modified, read and save its current content.
4. Apply all non-destructive edits.
5. If there are proposed destructive edits, present them to the user as a single batched approval request (one prompt per paper). User can approve all, reject all, or selectively approve. Apply approved edits.
6. **Last:** append the log entry to `wiki/log.md`.

**On failure at any step after the rollback journal exists:** roll back: restore each touched page to its journaled state (delete newly-created pages; restore original content for modified pages). Do not write the log entry. The next invocation will rediscover the paper as new and retry cleanly.

Do not implement partial-resume logic. The journal guarantees retry is always safe.

After each paper finishes, move to the next. Do not batch papers.

---

## Post-log: update `references/references.bib`

After **all** papers have been ingested and logged, invoke `/bib-update` in append-only mode. It reads the `## Bibliographic metadata` blocks from each newly-ingested paper's `_text.md`, runs the DOI-direct → CrossRef → OpenAlex → LLM-fallback cascade, and appends new entries to `references/references.bib`. Papers already present in `.bib` are skipped automatically.

To regenerate `.bib` from scratch, run `/bib-update --rebuild-bib` as a separate, explicit step — not as part of a normal ingest run.

---

## End-of-run summary

After all papers are processed, report:

- Papers successfully ingested (with counts of pages created/modified, and for Protocol M: figures copied)
- Papers that failed (with brief reasons; user can re-invoke to retry)
- Any disambiguation decisions the user made
- Any equation-fallback transcriptions marked "[unreadable equation]" (so the user can manually fix them)
- **Pending figure clips (punch-list).** Aggregate every CLIP placeholder from all Protocol E and S subagents:

  ```
  Pending figure clips (N):
    1. references/wiki/figures/Smith_2024_AER_fig2.png
       Smith_2024_AER, p. 14 — "DAG of identification strategy"
    ...
  ```

  Open each PDF to the indicated page, clip the figure, save under the listed path. Wiki pages already reference these paths — broken-image placeholders resolve silently as each PNG is added.

---

## Rules

- **Never modify source PDFs in `references/raw/` without approval.** Canonical renames require the batched approval flow. `_text.md` extracts are generated artifacts and may be created by Protocol M/S; Protocol E treats existing `_text.md` extracts as canonical input and does not rewrite them.
- **Never read PDF extracts, markdown, or splits in the main session.** Always delegate deep reading to subagents. The main session's job is orchestration and approval.
- **Never write the log entry before wiki edits complete.** The log is the source of truth for "what's been ingested" — it must lag behind, not lead.
- **Never invent project context.** If `CLAUDE.md` placeholders are unfilled, stop and ask. Do not guess the research question.
- **Project conventions in `references/CLAUDE.md` override this skill** if they conflict on format/naming/citation. This skill owns workflow only.
- **Never rename a PDF without user approval.** Even a single non-conforming file goes through the batched propose/approve flow. No silent `mv`. No overwriting an existing file.
- **Never fall back from the converter silently.** If `convert.py` errors on a PDF, report the error and proceed to tier E or S for that paper — do not substitute pdftotext output without telling the user.
- **Never use `pdftotext` for substantive ingest.** `pdftotext` is limited to first-page metadata/filename/bootstrap checks. It must not be used to summarize, validate, or supplement Protocol M or Protocol E content.
