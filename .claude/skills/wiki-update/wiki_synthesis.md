# Wiki Synthesis Prompt

Use this prompt after a project-neutral `_text.md` exists.

## Inputs

- `references/raw/<basename>_text.md`
- canonical paper basename
- `references/CLAUDE.md`
- project root `CLAUDE.md`
- current `references/wiki/index.md`
- relevant existing wiki page paths
- optional `references/raw/raw_build/<basename>_citation_overlap.json`
- optional cache `markdown.md` path, cache figure directory, absolute project `references/wiki/figures` directory, and `copy_marker_figure.py` path for Protocol M figure copies

Do not read worker notes, marker chunks, or the full marker `markdown.md`. If `_text.md` explicitly marks a gap that blocks wiki writing, return the gap to the main session instead of reopening fanout internals.

## Task

Use the neutral `_text.md`, project context, current index, and relevant existing pages to write project-specific wiki artifacts. Preserve the source paper's factual content, but interpret relevance through the project research question, data, and identification strategy.

## Source Page Naming

Use the canonical source slug from the paper basename:

- `Last_Year_Venue` -> `last-year-venue.md`
- `Last1_Last2_Year_Venue` -> `last1-last2-year-venue.md`
- `Last1_etal_Year_Venue` -> `last1-etal-year-venue.md`

Do not expand `_etal` into all author names. Examples:

- `Bento_Miller_Mookerjee_Severnini_2023_JEEM` -> `bento-etal-2023-jeem.md`
- `Anderson_etal_2022_NBER` -> `anderson-etal-2022-nber.md`

## Concept Page Rules

- Read `wiki/index.md` first.
- Reuse near-matching existing concept pages. Do not create duplicate synonyms.
- If a near-match exists but fit is ambiguous, return a disambiguation question.
- New concept pages need short, stable slugs that name concepts, not paper-specific prose.

## Project Interpretation Checks

When the project context concerns pollution, health, warning systems, or fiscal externalities, preserve details that often decide interpretation:

- sign conventions for health outcomes versus pollution production
- formal gap expressions such as `\beta^S - \beta^N`
- county-month norm definitions and any estimating equation window, including 5-year norms where used
- wind-IV extensions and alert/forecast identification threats
- payer decomposition such as Medicare/government versus out-of-pocket spending
- welfare bounds such as `\beta_A^{gov} \le \Delta W \le \beta_A^{gov} + \beta_A^{OOP}`
- conservative standard-error wording: when sources conflict, use the larger SE or smaller absolute t-stat

These are not mandatory claims. Include them only when supported by `_text.md` or existing wiki context.

## Outputs

- source page and concept/wiki pages
- non-destructive index updates
- proposed destructive diffs, if needed
- copied Protocol M figures, if relevant and available
- return-value summary required by `common.md`
