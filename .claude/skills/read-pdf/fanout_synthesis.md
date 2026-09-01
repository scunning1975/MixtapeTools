# Fanout Synthesis Prompt

Use this prompt after all worker bundles have durable notes.

## Inputs

- `manifest.json`
- all worker note paths
- output `_text.md` path
- `extraction_schema.md`

## Task

Read the manifest and every worker note. Write one coherent, project-neutral `_text.md` using `extraction_schema.md`.

Required output order:

1. Optional top-level paper title (`# ...`) if useful.
2. `## Bibliographic metadata`
3. `## Plain-English synthesis`
4. `## Research dimensions`, with dimensions 1 through 12 in schema order.

Do not put the bibliographic metadata block after the research dimensions.

## Rules

- Treat worker notes as local evidence, not final interpretation.
- Do gap-directed rereads only: reread source chunks when notes omit a needed table, figure, equation, result, or ambiguous claim.
- Do not read the full marker `markdown.md`.
- Do not read project wiki pages, project context files, citation-overlap JSON, or downstream workflow files.
- Do not write source pages, concept/wiki pages, index entries, log entries, or figure files.
- Preserve exact coefficients, standard errors, sample details, equation labels, and table/figure captions when available.
- Keep `_text.md` project-neutral. Downstream skills apply project relevance gates after this file exists.

## Outputs

- `<basename>_text.md`
