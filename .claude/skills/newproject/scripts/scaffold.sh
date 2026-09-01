#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
  echo "Usage: scaffold.sh <project-name> [parent-directory]" >&2
  exit 2
fi

raw_name="$1"
parent_dir="${2:-$PWD}"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(cd "$script_dir/.." && pwd)"
template_dir="$skill_dir/templates"

project_name="$(
  printf '%s' "$raw_name" \
    | tr '[:upper:]' '[:lower:]' \
    | sed -E 's/[[:space:]_]+/-/g; s/[^a-z0-9.-]+/-/g; s/^-+//; s/-+$//'
)"

if [ -z "$project_name" ]; then
  echo "Project name normalizes to empty: $raw_name" >&2
  exit 1
fi

mkdir -p "$parent_dir"
parent_abs="$(cd "$parent_dir" && pwd)"
project_root="$parent_abs/$project_name"

if [ -e "$project_root" ] && [ "$(find "$project_root" -mindepth 1 -maxdepth 1 2>/dev/null | head -n 1)" ]; then
  echo "Project directory already exists and is not empty: $project_root" >&2
  exit 1
fi

mkdir -p "$project_root"/{code/{download,data/validation,analysis/{stata,R,python}},data/{raw,clean},output/{figures,tables,logs},documents,references/raw,decks,notes,agent_memory,correspondence,progress_logs}

render_template() {
  local source="$1"
  local target="$2"

  sed \
    -e "s|{{PROJECT_ROOT}}|$project_root|g" \
    -e "s|{{PROJECT_NAME}}|$project_name|g" \
    "$source" > "$target"
}

for filename in config.do config.py config.R requirements.txt; do
  render_template "$template_dir/$filename" "$project_root/code/$filename"
done

render_template "$template_dir/project_CLAUDE.md" "$project_root/CLAUDE.md"
sed -i.bak "s/^## Project Overview$/## Project Overview — $project_name/" "$project_root/CLAUDE.md"
rm -f "$project_root/CLAUDE.md.bak"

cat > "$project_root/agent_memory/key_decisions.md" <<EOF
# Key Decisions — $project_name

Running log of methodological decisions. Append new rows; do not edit prior entries.

| Date | Decision | Rationale |
|------|----------|-----------|
EOF

cat > "$project_root/agent_memory/dropped_analyses.md" <<EOF
# Dropped Analyses — $project_name

Analyses tried and abandoned — so they don't get re-suggested.

- **[Analysis name]** ([YYYY-MM-DD]): [Why dropped]
EOF

cat > "$project_root/agent_memory/codebook.md" <<EOF
# Codebook — $project_name

Definitions of key variables, especially constructed ones.

| Variable | Definition | Source |
|----------|------------|--------|
EOF

cat > "$project_root/agent_memory/sample_restrictions.md" <<EOF
# Sample Restrictions — $project_name

Who's in the sample and why. Document exclusions with counts.

- [Restriction]: [Rationale] ([N excluded])
EOF

cat > "$project_root/README.md" <<EOF
# $project_name

One-line project description goes here.

## Overview

Fill in the project overview, research question, data sources, and identification strategy in \`CLAUDE.md\`.

## Directory Structure

\`\`\`
$project_name/
├── CLAUDE.md
├── README.md
├── code/
│   ├── config.do
│   ├── config.py
│   ├── config.R
│   ├── requirements.txt
│   ├── download/
│   ├── data/validation/
│   └── analysis/{stata,R,python}/
├── data/{raw,clean}/
├── output/{figures,tables,logs}/
├── documents/
├── references/raw/
├── decks/
├── notes/
├── agent_memory/
├── correspondence/
└── progress_logs/
\`\`\`

## Folder Notes

- \`data/raw/\` stores immutable source data; cleaning outputs go to \`data/clean/\`.
- \`code/config.*\` files define canonical paths. Update \`root\` if the project moves.
- \`output/\` stores generated figures, tables, and logs.
- \`references/raw/\` stores PDFs for \`/split-pdf\`, \`/read-pdf\`, \`/bib-update\`, and \`/wiki-update\`.
- \`references/wiki/\` and \`references/references.bib\` are created lazily by reference skills.
- \`agent_memory/\` stores durable decisions, codebook notes, dropped analyses, and sample restrictions.
- \`progress_logs/\` maintains continuity across Claude/Codex sessions.

## Collaborators

- [Name]: [Role]

## Status

- [Current status]

## Key Files

- [Add important files here as the project develops]
EOF

today="$(date +%F)"
cat > "$project_root/progress_logs/${today}_setup.md" <<EOF
# Setup Log — $project_name

**Date:** $today

## Created

- Standard research project directory structure
- Root \`CLAUDE.md\` from template
- Language config files in \`code/\`
- Agent memory stubs
- Project README

## Next Steps

- Fill in the Project Overview in \`CLAUDE.md\`
- Add data sources or acquisition scripts
- Update \`code/requirements.txt\` as Python dependencies become known
- Initialize git separately when ready (\`git init\`, \`.gitignore\`, etc.)
EOF

printf '%s\n' "$project_root"
