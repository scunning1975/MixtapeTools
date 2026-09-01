---
name: newproject
description: Scaffold a new research project with standard directory structure, CLAUDE.md template, and language-agnostic config files (Stata/Python/R). Use this at the start of every new project to ensure consistent organization.
allowed-tools: Bash(mkdir*), Bash(cp*), Bash(ls*), Write, Read
argument-hint: [project-name]
---

# New Project Scaffold

Create a new research project folder with the standard structure.

## Templates

All templates are stored locally in the skill at `~/.claude/skills/newproject/templates/`:

- `project_CLAUDE.md` — project root CLAUDE.md
- `config.do`, `config.py`, `config.R` — canonical paths for Stata / Python / R
- `requirements.txt` — Python dependencies stub

Templates use `{{PROJECT_ROOT}}` and `{{PROJECT_NAME}}` placeholders that this skill substitutes at scaffold time.

## What Gets Created

```
[project-name]/
├── CLAUDE.md                          # Research rules (from template)
├── README.md                          # Project-specific overview (auto-generated)
├── code/
│   ├── config.do                      # Canonical Stata globals & paths
│   ├── config.py                      # Canonical Python paths (pathlib)
│   ├── config.R                       # Canonical R paths
│   ├── requirements.txt               # Python dependencies
│   ├── download/                      # Scripts for pulling raw data
│   ├── data/
│   │   └── validation/                # Data validation scripts
│   └── analysis/
│       ├── stata/
│       ├── R/
│       └── python/
├── data/
│   ├── raw/                           # Original source data (never modify)
│   └── clean/                         # Cleaned/merged datasets
├── output/
│   ├── figures/
│   ├── tables/
│   └── logs/                          # Log files from all scripts
├── documents/                         # Outside PDFs, papers
├── references/
│   └── raw/                           # PDFs for split-pdf/read-pdf/wiki-update/bib-update
├── decks/                             # Beamer presentations
├── notes/                            # Personal scratch notes; ignored by git in git-enabled projects
├── agent_memory/                      # Shared Claude/Codex reference files for this project
├── correspondence/                   # Letters, emails, referee reports (subdirs created lazily by /referee2 and /blindspot)
└── progress_logs/                    # Session continuity logs
```

## Execution

### Step 1 — Get project name
If no argument was provided, ask:
> "What should I name this project? (will be used as the folder name and in templates)"

Normalize: lowercase, spaces → hyphens.

### Step 2 — Determine location
Default to current working directory. If unclear, confirm with the user.

Set `PROJECT_ROOT` = `[location]/[project-name]` as an absolute path.

### Step 3 — Create all directories

```bash
mkdir -p [project-name]/{code/{download,data/validation,analysis/{stata,R,python}},data/{raw,clean},output/{figures,tables,logs},documents,references/raw,decks,notes,agent_memory,correspondence,progress_logs}
```

### Step 4 — Render config files from templates

For each of `config.do`, `config.py`, `config.R`, `requirements.txt`:
1. Read `~/.claude/skills/newproject/templates/<filename>`
2. Substitute `{{PROJECT_ROOT}}` with the absolute project root path, and `{{PROJECT_NAME}}` with the normalized project name
3. Write to `[project-name]/code/<filename>`

### Step 5 — Create `CLAUDE.md` from template

Read `~/.claude/skills/newproject/templates/project_CLAUDE.md`.
Write it to `[project-name]/CLAUDE.md` as-is.
Update the Project Overview section heading to reference the project name.

### Step 5b — Create index stubs in `agent_memory/`

CLAUDE.md points to these files rather than embedding their content. Create each as an empty stub so Claude and the user have a known location to append to.

**`agent_memory/key_decisions.md`**:
```markdown
# Key Decisions — [project-name]

Running log of methodological decisions. Append new rows; do not edit prior entries.

| Date | Decision | Rationale |
|------|----------|-----------|
```

**`agent_memory/dropped_analyses.md`**:
```markdown
# Dropped Analyses — [project-name]

Analyses tried and abandoned — so they don't get re-suggested.

- **[Analysis name]** ([YYYY-MM-DD]): [Why dropped]
```

**`agent_memory/codebook.md`**:
```markdown
# Codebook — [project-name]

Definitions of key variables, especially constructed ones.

| Variable | Definition | Source |
|----------|------------|--------|
```

**`agent_memory/sample_restrictions.md`**:
```markdown
# Sample Restrictions — [project-name]

Who's in the sample and why. Document exclusions with counts.

- [Restriction]: [Rationale] ([N excluded])
```

### Step 6 — Generate `README.md`

Include:
- Project title and one-line description placeholder
- Visual directory tree (fenced code block matching structure above)
- Explanation of each folder's purpose
- Note that `references/raw/` stores paper PDFs for `/split-pdf`, `/read-pdf`, `/bib-update`, and `/wiki-update`; `references/wiki/` and `references/references.bib` are created lazily by those skills
- Note that `CLAUDE.md` is from a permanent template — edit per-project
- Note that `code/config.*` files define all paths — update `root` if project moves
- Note that `progress_logs/` maintains continuity across Claude sessions
- Placeholder sections: Overview, Collaborators, Status, Key Files

### Step 7 — Create initial progress log

Write `progress_logs/[YYYY-MM-DD]_setup.md`:
- Creation date
- Checklist of standard next steps (add data sources, fill in CLAUDE.md, etc.)

### Step 8 — Report success

Show the created structure with `ls -R [project-name] | head -60`.
Remind the user to:
- Fill in the Project Overview in `CLAUDE.md`
- Update `code/config.*` files if the project root ever moves
- Add Python packages to `code/requirements.txt` as needed
