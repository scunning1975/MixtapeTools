# Wiki-Update (`/wiki-update`)

`/wiki-update` ingests new PDFs from a project's `references/raw/` folder into the project's literature wiki. It summarizes each paper through the lens of the project's research focus, writes or updates wiki pages, records completed ingests, and refreshes BibTeX metadata.

The executable protocol lives in [`SKILL.md`](SKILL.md). This README is the human overview.

## When To Use It

Use `/wiki-update` after adding one or more PDFs to `references/raw/`.

Natural-language triggers include:

- "ingest new references"
- "update the wiki"
- "process the new papers I added"

The skill is designed to be safe to re-run. Completed papers are identified from the wiki log; unfinished papers are rediscovered and retried.

## What It Expects

- `references/raw/` for source PDFs.
- `references/wiki/` for concept pages and the ingest log.
- `references/CLAUDE.md` for wiki conventions.
- A project root `CLAUDE.md` with the research question, data sources, and identification strategy filled in.

On first run, the skill can scaffold the references wiki structure. It will not invent missing project context.

## What It Does

- Finds new PDFs and proposes filename normalization.
- Reads each paper in isolated subagents to avoid PDF image bloat and whole-file markdown reads in the main session.
- Reuses existing `_text.md` extracts or PDF splits when available.
- For marker-converted PDFs, writes a neutral `_text.md` first, then runs a separate project-wiki synthesis pass.
- Applies a project-context relevance filter so important material receives full treatment and less relevant material gets concise page-referenced notes.
- Writes wiki pages atomically per paper, then logs completion only after edits succeed.
- Runs the BibTeX update cascade after ingestion.

## Boundaries

`/wiki-update` owns the project-wiki lifecycle. `/read-pdf` owns standalone paper reading, including the `/read-pdf --split` fallback. The two skills share the same batching idea, but `/wiki-update` uses a non-interactive subagent flow because a per-batch confirmation gate would deadlock inside an ingest subagent.

For exact tier rules, destructive-edit handling, filename checks, log format, and BibTeX behavior, read [`SKILL.md`](SKILL.md).

## Related Skills

- `/newproject` — creates the project structure this skill expects.
- `/read-pdf` — standalone paper reading and reusable `_text.md` extraction.
- `/read-pdf --split` — standalone batched vision reading for individual papers.
- `/bib-update` — refreshes `references/references.bib` from extracted metadata.

---

The conceptual foundation for this skill is owed to [Andrej Karpathy's LLMwiki concept](https://x.com/karpathy). `/wiki-update` operationalizes that idea for empirical-economics workflows.

This skill originated in [Scott Cunningham](https://github.com/scunning1975/MixtapeTools)'s MixtapeTools repository.
