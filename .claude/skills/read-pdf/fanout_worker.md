# Fanout Worker Prompt

Use this prompt for one bounded worker bundle from `prepare_substrate.py`.

## Inputs

- bundle id and bundle excerpt from `worker_bundles`
- output note path
- position: `front_matter`, `body`, `back_matter`, or `full_paper`

## Task

Read only assigned chunk paths. Write local extraction notes to the output note path. Do not write paper-level conclusions, `_text.md`, wiki pages, index entries, or log entries.

## Position-Specific Emphasis

`front_matter`:
- Bibliographic candidates: title, authors, year, venue, DOI.
- Abstract, introduction framing, research question, stated contribution.
- Any early equations, figures, or tables.

`body`:
- Local evidence only: methods, data, specifications, findings, tables, figures, and equations found in assigned chunks.
- Do not reconstruct bibliography unless assigned chunks contain new or contradictory metadata.

`back_matter`:
- Robustness, appendices, limitations, replication/data availability, and references-section clues.
- Record references only when they matter for DOI/bibliographic candidates or citation-overlap checks.

`full_paper`:
- Apply all extraction categories across the assigned chunks. Do not over-prioritize title/abstract material just because the paper fit in one bundle.

## Note Format

```markdown
# Worker notes: <bundle_id>

## Source chunks
- <chunk path> — <heading>

## Local extraction
- Research question / motivation evidence:
- Method / identification evidence:
- Target parameter evidence:
- Data evidence:
- Statistical methods / specifications:
- Findings:
- Contributions:
- Replication feasibility:

## Formal-object inventory
- Tables:
- Figures:
- Equations/specifications:
- Other formal objects:

## Bibliographic candidates
- doi:
- authors:
- title:
- year:
- venue:

## Unresolved gaps
- <specific missing item or ambiguity, with source location>
```

Preserve exact numbers, equation labels, table/figure captions, and page anchors when present. Keep notes compact, but do not omit formal objects.
