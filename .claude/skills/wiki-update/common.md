# Common protocol fragments — wiki-update subagent

These sections are shared across Protocols M, E, and S. The main session passes this file by path into every per-paper subagent prompt, alongside exactly one of `protocol_m.md`, `protocol_e.md`, or `protocol_s.md`.

---

## `_text.md` structure

Protocols that synthesize `_text.md` (Protocol S and the read-pdf fanout synthesis used by Protocol M) use this layout:

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
[continue through dimension 12]
```

## Plain-English synthesis block

Hard cap: ~200 words. No jargon. Cover:

- Research question (1 sentence)
- Motivation / why it matters (1–2 sentences)
- What they estimate and how, in plain terms (2–3 sentences)
- What they found (1–2 sentences)
- The take-away — what someone should walk away believing or doing differently (1 sentence)

This block is the answer to "what's this paper about?" for someone who will not read the rest. Anyone with a college degree should be able to read it without a glossary. If you find yourself writing "endogeneity" or "LATE" or "first-stage F-stat," rewrite in plainer terms.

## Structured-extraction dimensions

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
12. **Equations / formal objects** — labeled equations, model primitives, algorithms, propositions, and other formal objects needed to understand or replicate the paper

## Tables protocol (project-relevance gated)

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

## Figures protocol (project-relevance gated, two-tier)

Apply the project-relevance filter. Non-relevant figures: one-line description with page reference only.

For relevant figures, classify as Tier A or Tier B using caption text:

- **Tier A — Data figures**: scatter, line, bar, coefplot, histogram, density, time series, RD/event-study plot. The data IS the content.
- **Tier B — Schematic figures**: DAGs, conceptual diagrams, maps, flowcharts, theoretical model schematics. Do NOT attempt optical decomposition. Default to Tier B when uncertain — a structured Tier A block written for a schematic is misleading; a Tier B for a data figure just makes the reader look at the image.

**In `_text.md`:**

*Protocol M* — figures are copied to `references/wiki/figures/`. Record:

```
**Figure N:** <verbatim caption> (p. 12)
![<short description>](figures/<basename>_figN.<ext>)
- Type: <for Tier A: scatter / line / bar / etc.>
- X-axis: <variable, units, range>    [Tier A only]
- Y-axis: <variable, units, range>    [Tier A only]
- Series / panels: <brief list>       [Tier A only]
- Key visual finding: <one sentence>
- Annotations: <labels, reference lines, shaded regions>  [Tier A only]
- **Figure notes:** <verbatim notes below the figure, if any>
[Tier B: replace the structured block with just: One-liner: <what the figure depicts at a glance>]
```

All wiki source pages and concept pages are written directly under `references/wiki/`, so embedded figure links must be relative to that directory. For Protocol M, use the path printed by `copy_marker_figure.py`, usually `figures/<basename>_figN.jpg` or `figures/<basename>_figN.png`. Do not use `../figures/...` or `../wiki/figures/...` in wiki pages.

*Protocols E and S* — use CLIP placeholders (described in their respective protocol sections).

## Substantive-change rule

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

## Concept page disambiguation

Before creating a new concept page, check `wiki/index.md` for existing pages covering the same concept — including obvious synonyms (e.g., "RDD" vs "regression discontinuity"). If a near-match exists but you aren't confident, do **not** create a new page; return the ambiguity to the main session as a question for the user.

## Relevance filtering

Apply "compress, don't omit": sections directly relevant to the project's research focus get full treatment. Less-relevant sections get a one-line description plus page reference. Nothing is fully omitted.

## Subagent return value

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
