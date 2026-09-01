---
name: bibcheck
description: Many-agent bibliography audit. Verify each citation in a .bib file by spawning narrow-focus agents that confirm DOI/URL and cross-check that all fields belong to the same paper. Catches mixed-up entries (one paper's title with another's authors), wrong years, journal misattributions, and unverifiable references. Use when reviewing a manuscript's bibliography for accuracy before submission, after literature review, or when inheriting a .bib from a coauthor.
allowed-tools: Bash(claude*), Bash(ls*), Bash(cat*), Bash(wc*), Bash(grep*), Bash(mkdir*), Bash(cp*), Bash(~/.claude/skills/bibcheck/scripts/split_bib.py:*), Read, Write, Edit, WebSearch, WebFetch, Agent
argument-hint: '[--by-citation|--by-field] <path-to-bib-or-tex> [--max-parallel N]'
---

# Bibcheck: Many-Agent Bibliography Audit

You are running `/bibcheck` — a verification routine that audits a bibliography by spawning many narrow-focus agents, one per citation (or one per field), so each agent operates on a small task with low risk of attention decay over a long context.

## Why narrow agents

See `methodology.md` for the full gradient-decay rationale and audit standard.

## Step 0: Read your full methodology

1. Read `methodology.md` in this skill directory — it explains the gradient-decay rationale and the audit standard for both modes.
2. Confirm you understand which mode the user invoked.

## Step 1: Parse arguments

Modes:

| Argument | Mode | What it does |
|----------|------|--------------|
| `--by-citation <file>` (default if omitted) | **Per-citation** | One Agent subagent per bib entry. Each fully audits its one entry. |
| `--by-field <file>` | **Per-field** | One CLI subprocess per field (title, year, journal, authors, volume/issue, pages, DOI). Each specialist reads the whole bibliography but checks only its field. |
| `--max-parallel N` | Optional | Cap concurrent subagents/subprocesses. Default 8. |

Input file:
- `.bib` — use directly
- `.tex` — extract `\bibitem{}` blocks or read the linked `.bib` from `\bibliography{}`. If both a `.tex` and a `.bib` are in the same folder, prefer the `.bib`.

If the user invoked `/bibcheck` with no arguments, ask:
- Which mode? (per-citation is the default; per-field is for adversarial cross-checks)
- Path to the .bib or .tex?

Do not guess.

## Step 2: Set up the run directory

For `.bib` input, run the splitter:

```bash
~/.claude/skills/bibcheck/scripts/split_bib.py path/to/references.bib
```

It creates:

```
<bib_dir>/bibcheck_<timestamp>/
  ├── input.bib              # copy of source
  ├── entries/               # split entries (one .bib per entry)
  ├── reports/               # per-agent JSON/markdown outputs
  ├── bibcheck_report.md     # final consolidated report
  └── corrected.bib          # drop-in replacement
```

The timestamped folder means re-runs do not clobber prior audits.

For `.tex` input, first resolve the linked `.bib` or extract `\bibitem{}` blocks into `input.bib`, then use the same run directory shape.

## Step 3: Run the selected mode

Read the mode-specific protocol file and follow it end-to-end. Only one of these fires per invocation:

- **Per-citation mode** (`--by-citation`, default): see `mode_per_citation.md`. One Agent subagent per `.bib` entry; each fully audits its single entry; final reviewer consolidates.
- **Per-field mode** (`--by-field`): see `mode_per_field.md`. One isolated `claude -p` subprocess per field; each specialist checks only its field across the whole bibliography; consolidator joins by entry key.

## Step 4: Present the result to the user

Show the user:

```
bibcheck complete.

  Clean:        N entries
  Corrected:    M entries (see bibcheck_report.md)
  Unverifiable: K entries (need human eyes)

Drop-in replacement: corrected.bib
Full audit:          bibcheck_report.md
```

Do not auto-overwrite the user's source `.bib`. They review, then move `corrected.bib` into place themselves.

## Defaults and tone

- Default mode is **per-citation** unless the user asks for `--by-field`.
- Default `--max-parallel` is **8**. Bump on request.
- This is a verification skill — never *write* citations from scratch. Only audit and correct.
- If a citation is genuinely unverifiable (paywalled, dead URL, ambiguous match), say so. Do not invent a DOI.

## When to suggest the other mode

After per-citation completes, if 3+ entries came back as unverifiable, suggest the user re-run with `--by-field` for those specific entries — a field-specialist sometimes catches what a citation-generalist missed (e.g., a wrong year hiding behind a correct title).
