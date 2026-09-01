# Skills for Claude Code

## What is this?

[Claude Code](https://docs.anthropic.com/en/docs/claude-code) is a way to work with Claude directly on your computer — you type instructions, and Claude reads files, writes code, searches the web, and carries out tasks for you. If you've used Claude in the browser, Claude Code is the version that can actually *do things* on your machine.

**Skills** are pre-written workflows for Claude Code. Think of them as recipes. You type a short command (like `/split-pdf`), and Claude follows a detailed set of instructions to carry out a complex, multi-step task automatically. Without the skill, you'd have to explain every step yourself each time. With the skill, it's one command.

This directory contains documentation, methodology, and example output for the skills in this repo. Browse what's available below.

---

## Available Skills

| Skill | Command | What it does |
|-------|---------|--------------|
| [**Referee 2**](referee2/) | `/referee2` | A five-audit systematic review protocol — code correctness, cross-language replication, directory structure, output automation, and econometrics. Runs in a fresh terminal after project completion. Creates independent replication scripts in two additional languages and files a formal referee report with verdict. [See documentation →](referee2/) |
| [**Blindspot**](blindspot/) | `/blindspot` | A peripheral vision audit for empirical output. Finds what the author cannot see — problems hiding in plain sight (**vices**: the unexplained feature, the convenient absence) and opportunities being overlooked (**virtues**: the unasked question, the unexploited strength). Inspired by Viktor Shklovsky's defamiliarization principle: art exists to make the stone stony again. [See documentation →](blindspot/) |
| [**Beautiful Deck**](beautiful_deck/) | `/beautiful_deck` | End-to-end beautiful deck creation. Designs an original Beamer `.sty` (or Quarto/Typst style) per audience, restructures content via the Rhetoric of Decks with the pedagogical movement Narrative → Application → Picture → Codeblock → Technical, generates figures code-first, **writes safe TikZ from the start** using explicit node dimensions, coordinate maps, and canonical templates (Step 4.4), compiles to zero warnings, runs `/tikz` for residual collision repair, and dispatches rhetoric + graphics audit sub-agents. The key insight: prevention in Step 4.4 is worth ten repair passes in Step 6. [See documentation →](beautiful_deck/) |
| [**Compile Deck**](compiledeck/) | `/compiledeck` | The mechanical compile loop — preamble templates, palette reference, and TikZ rules. Called by `/beautiful_deck` for compile mechanics. Use directly when editing an existing deck rather than building from scratch. [See documentation →](compiledeck/) |
| [**TikZ Audit**](tikz/) | `/tikz` | **A repair tool, not a safety net.** Finds and fixes residual visual collisions in TikZ figures using measurement, not intuition — six-pass protocol covering Bézier curve depths, edge-label gap calculations, boundary clearances, and cross-slide consistency. Catches what `pdflatex` misses. But it cannot reliably fix diagrams that were never built with measurement in mind. The upstream defense is `/beautiful_deck` Step 4.4, which writes safe TikZ from the start. `/tikz` is the downstream check. [See documentation →](tikz/) |
| [**Split-PDF**](split-pdf/) | `/split-pdf` | Downloads and deep-reads academic PDFs without crashing the session. Uses the PDF in place (no centralized `articles/` folder), splits into 4-page chunks in a `_build/` directory, reads in batches of ~12 pages, writes structured notes, and saves a persistent `_text.md` extraction so future invocations skip re-reading. When called by another skill, reads inside a subagent to prevent context bloat. [See full walkthrough →](split-pdf/) |
| [**Wiki Update**](wiki-update/) | `/wiki-update` | Ingests PDFs from `references/raw/` into a project-specific markdown wiki. Uses project context from `CLAUDE.md`, routes paper reading through `/read-pdf`, cached extracts, or split-PDF fallback, gates destructive wiki edits behind approval, and hands BibTeX maintenance to `/bib-update`. [See documentation →](wiki-update/) |
| [**Bibcheck**](bibcheck/) | `/bibcheck` | Many-agent bibliography audit. Spawns one narrow-focus agent per citation (or one specialist per field) to verify each `.bib` entry against canonical sources — DOI, journal landing page, author working paper. Catches the silent errors a single-agent audit misses as attention decays across long lists: mixed-up entries (title of paper A with authors of paper B), wrong years, journal misattributions. Per-field mode launches each specialist as an isolated `claude -p` subprocess so they cannot peek at each other's conclusions. Outputs a `bibcheck_report.md` and a drop-in `corrected.bib`. [See documentation →](bibcheck/) |
| [**New Project**](newproject/) | `/newproject` | Scaffolds a new research project with standard directory structure, CLAUDE.md template, and documented README. [See documentation →](newproject/) |
| [**New Book**](newbook/) | `/newbook` | Scaffolds a book-shaped project: `memoir`-based LaTeX skeleton, Palatino body, Gov 2001 palette, voiced-sidebar `\voice{<name>}{<text>}` callouts, one chapter per file, bibliography stub, `CLAUDE.md` with voice and lineage rules, `% SUBSTACK MAP:` placeholders in each chapter, and a chapter-per-file structure that converts cleanly to HTML later. Parallel to `/newproject`. This is the skill that produced *AI Agents and the Research Worker*. [See documentation →](newbook/) |

---

## How to Use These Skills

**Prerequisites:** You need [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed. If you haven't set it up yet, follow Anthropic's installation guide first.

**Then:**

1. **Clone this repo** (or just copy the `.claude/skills/` directory — that's the hidden folder where the actual skill instructions live)
2. Place the `.claude/skills/` folder in your project root
3. Open Claude Code in that project directory
4. Type the slash command: `/split-pdf "Gentzkow Shapiro 2014 competition newspapers"`

That's it. Claude Code automatically discovers skills in `.claude/skills/` and makes them available as slash commands. No configuration needed.

---

## Why are there two directories?

You might notice this repo has both a visible `skills/` folder (what you're reading now) and a hidden `.claude/skills/` folder. Here's why:

- **`.claude/skills/`** contains the actual skill files — the instructions Claude follows when you invoke a command. These are written *for Claude*, in a format it understands (step-by-step imperatives with metadata). This directory is hidden on GitHub because it starts with a dot.

- **`skills/`** (this directory) contains documentation *for you* — what each skill does, why it works, how to use it, and examples of real output. It's the human-readable companion to the machine-readable instructions.

When you clone the repo, you get both. Claude reads its instructions from `.claude/skills/`. You read the documentation here in `skills/`.

---

## How Skills Work (Under the Hood)

Each skill is a markdown file at `.claude/skills/<name>/SKILL.md`. It has a small header (metadata) that tells Claude Code the skill's name and what tools it's allowed to use, followed by step-by-step instructions that Claude follows when you invoke the command.

```
.claude/skills/
├── referee2/
│   └── SKILL.md           # The instructions Claude follows
├── blindspot/
│   └── SKILL.md           # The instructions Claude follows
├── compiledeck/
│   ├── SKILL.md           # The instructions Claude follows
│   ├── domain_patterns.md # Audience-specific guidance
│   ├── palette_reference.md # Color palette options
│   └── tikz_rules.md      # TikZ collision-prevention protocol
├── split-pdf/
│   ├── SKILL.md           # The instructions Claude follows
│   └── methodology.md     # Why this approach works (for humans)
├── bibcheck/
│   ├── SKILL.md           # The instructions Claude follows
│   └── methodology.md     # Why narrow agents beat one big audit (for humans)
├── newproject/
│   └── SKILL.md           # The instructions Claude follows
└── newbook/
    ├── SKILL.md           # The instructions Claude follows
    └── templates/         # File templates the scaffold uses

skills/
├── referee2/
│   └── README.md          # Five audits, the R&R process, how it works
├── blindspot/
│   └── README.md          # Shklovsky, the vice/virtue grid, origin story
├── compiledeck/
│   └── README.md          # The Rhetoric of Decks, palettes, TikZ rules
├── split-pdf/
│   └── README.md          # Full documentation and examples (for humans)
├── bibcheck/
│   └── README.md          # Two modes, when to use each, cost and rate-limit notes
├── newproject/
│   └── README.md          # Philosophy, folder purposes, installation (for humans)
└── newbook/
    └── README.md          # Book-shaped scaffold; voiced sidebars; chapter-per-file structure
```

If you're curious what the actual instructions look like, you can read the [SKILL.md file directly](../.claude/skills/split-pdf/SKILL.md) — but you don't need to understand it to use the skill.

---

## Adding New Skills

To create your own skill:

1. Create a directory under `.claude/skills/` with a `SKILL.md` file
2. Optionally create a matching directory under `skills/` with a `README.md` for documentation

If you develop a useful skill for academic research, PRs are welcome.
