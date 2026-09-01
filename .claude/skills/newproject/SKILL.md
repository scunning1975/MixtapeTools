---
name: newproject
description: Scaffold a new research project with standard directory structure, CLAUDE.md template, and language-agnostic config files (Stata/Python/R). Use this at the start of every new project to ensure consistent organization.
allowed-tools: Bash(ls*), Bash(~/.claude/skills/newproject/scripts/scaffold.sh:*), Read
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

### Step 1 — Get project name and location
If no argument was provided, ask:
> "What should I name this project? (will be used as the folder name and in templates)"

Default to current working directory. If unclear, confirm with the user.

### Step 2 — Run scaffold script

Run:

```bash
~/.claude/skills/newproject/scripts/scaffold.sh "[project-name]" "[parent-directory]"
```

The script normalizes the project name, creates the directory tree, renders templates, writes agent-memory stubs, generates `README.md`, and creates the initial setup log. It prints the absolute project root.

### Step 3 — Report success

Show the created structure with `ls -R [project-name] | head -60`.
Remind the user to:
- Fill in the Project Overview in `CLAUDE.md`
- Update `code/config.*` files if the project root ever moves
- Add Python packages to `code/requirements.txt` as needed
