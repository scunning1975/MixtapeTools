# Protocol M — Fanout Extract Then Wiki Synthesis

*Input:* path to `manifest.json` produced by `read-pdf/scripts/prepare_substrate.py`, path to the converter cache directory (for figures and `text.md`), canonical paper basename.

Protocol M reads only `manifest.json`, its chunk files, worker notes, cache-local figure files, the neutral `_text.md`, and wiki context files. Do not read the whole converted `markdown.md`. Do not inspect the source PDF with `pdftotext` or any other text extractor for substantive synthesis, even if conversion is slow. If conversion or substrate preparation is still running, wait.

## Step 1: Extract bounded worker notes

The main session spawns one worker agent per `manifest.worker_bundles` entry, sequentially. Each worker receives its bundle excerpt, reads the assigned chunk paths only, follows `~/.claude/skills/read-pdf/fanout_worker.md`, and writes one durable note file under `references/raw/raw_build/<basename>_fanout/worker_notes/`.

If interrupted, completed worker notes are salvageable and should not be deleted.

## Step 2: Synthesize `_text.md`

After all worker notes exist, the main session spawns one read-pdf synthesis agent. The synthesis agent reads `manifest.json` and all worker note files. It uses `~/.claude/skills/read-pdf/fanout_synthesis.md` plus `~/.claude/skills/read-pdf/extraction_schema.md` to produce `references/raw/<basename>_text.md` following the project-neutral `_text.md` structure (bib block, plain-English synthesis, structured dimensions, and formal-object inventories). Gap-reread specific chunk files only when worker notes omit a needed table, figure, equation, result, or ambiguous claim. Write or overwrite if a prior partial file exists.

After the synthesis agent returns, cache the neutral extract with:

```bash
python3 ~/.claude/skills/read-pdf/scripts/cache_text.py push "<cache-dir>/markdown.md" "references/raw/<basename>_text.md"
```

This cache-level neutral extract is project-neutral and reusable by future projects that ingest the same PDF hash.

For the bib metadata block, use DOI candidates from `manifest.json` and front-matter worker notes. Extract authors, title, year, and venue from the front-matter chunks and worker notes. Record null for any field not found. Do not read the whole `markdown.md` for metadata.

The read-pdf synthesis agent must not read project wiki pages, project context files, citation-overlap JSON, or downstream wiki prompts. It writes only `_text.md`.

## Step 3: Write project wiki pages

After `_text.md` exists, the main session spawns one wiki synthesis agent. It reads:

- `references/raw/<basename>_text.md`
- `references/CLAUDE.md`
- project root `CLAUDE.md`
- current `references/wiki/index.md`
- relevant existing wiki pages
- `references/raw/raw_build/<basename>_citation_overlap.json`, if produced
- `~/.claude/skills/wiki-update/wiki_synthesis.md`
- `~/.claude/skills/wiki-update/common.md`

The wiki synthesis agent must not read worker notes or chunk files unless `_text.md` explicitly marks a gap and the main session approves a targeted recovery read.

## Step 4: Copy and classify relevant figures

For each relevant figure listed in `_text.md`:

1. Identify the paper figure number from surrounding caption text.
2. Apply the project-relevance filter. Non-relevant: one-line description + page ref only; do not copy.
3. For relevant figures:
   - Copy with the deterministic helper, not by hand:
     `python3 ~/.claude/skills/wiki-update/scripts/copy_marker_figure.py <cache-dir>/markdown.md <absolute-project-root>/references/wiki/figures --basename <basename> --figure <M>`
   - Use the helper's printed wiki-relative path in markdown. The helper preserves the source image format and uses a byte-matching extension, so destinations may be `.jpg` or `.png`.
   - Verify copied files exist with `ls references/wiki/figures/<basename>_fig<M>.*`.
   - Classify as Tier A (data figure: scatter, line, bar, coefplot, histogram, density, time series, RD/event-study plot) or Tier B (schematic: DAG, conceptual diagram, map, flowchart, theoretical model). Use the `_text.md` figure description and caption; read the PNG only if genuinely needed for wiki writing.

## Step 5: Wiki figure embeds

Use the substantive-change rule and relevance filtering in `common.md`.

For relevant figures embedded in wiki concept pages, use this format regardless of Tier A/B:

```markdown
**Figure N:** <verbatim caption> (p. 12)

![<short description>](<helper-printed-path>)

- Key visual finding: <one sentence — what the eye sees / the point of the figure>
- **Figure notes:** <verbatim notes printed below the figure in the paper, if any>
```

All wiki pages live directly under `references/wiki/`. Figure links must use the helper-printed path, e.g. `figures/<basename>_figN.jpg` or `figures/<basename>_figN.png`, never `../figures/...`.

The Tier A/B distinction lives in `_text.md` only (full optical decomposition for Tier A; schematic one-liner for Tier B). Wiki pages use the same lightweight embed format for all figures.

## Return value additions for Protocol M

```
Figures copied: [list of {source_cache_path, dest_wiki_path, paper_figure_label}]
Equation fallback used: <true/false> (with count and any "[unreadable equation]" instances if true)
```
