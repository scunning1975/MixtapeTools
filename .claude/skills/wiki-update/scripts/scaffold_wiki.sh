#!/usr/bin/env bash
# Idempotent: scaffolds references/ tree, renders references/CLAUDE.md from
# template, initializes wiki/index.md and wiki/log.md, and appends a wiki
# pointer to the project root CLAUDE.md if present.
#
# Usage: scaffold_wiki.sh [project-root]
#   project-root defaults to $PWD. Project name is the basename.
#
# Exits 0 on success (including the no-op case where everything already exists).

set -euo pipefail

project_root="${1:-$PWD}"
project_root="$(cd "$project_root" && pwd)"
project_name="$(basename "$project_root")"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(cd "$script_dir/.." && pwd)"
template="$skill_dir/templates/references_CLAUDE.md"

if [ ! -f "$template" ]; then
  echo "Template not found: $template" >&2
  exit 1
fi

# Directory tree (mkdir -p is idempotent).
mkdir -p \
  "$project_root/references/raw" \
  "$project_root/references/wiki" \
  "$project_root/references/wiki/figures"

# references/CLAUDE.md — render from template only if absent.
target_claude="$project_root/references/CLAUDE.md"
if [ ! -f "$target_claude" ]; then
  sed -e "s|{{PROJECT_NAME}}|$project_name|g" "$template" > "$target_claude"
fi

# wiki/index.md — initialize only if absent.
index="$project_root/references/wiki/index.md"
if [ ! -f "$index" ]; then
  cat > "$index" <<EOF
# Wiki Index — $project_name

| Page | Description |
|------|-------------|
EOF
fi

# wiki/log.md — initialize only if absent.
log="$project_root/references/wiki/log.md"
if [ ! -f "$log" ]; then
  cat > "$log" <<EOF
# Wiki Log — $project_name

| Date | Source | Changes |
|------|--------|---------|
EOF
fi

# Append a wiki pointer to project root CLAUDE.md, idempotent.
root_claude="$project_root/CLAUDE.md"
pointer_line="- See \`references/CLAUDE.md\` for wiki conventions and the project's reference library."
if [ -f "$root_claude" ] && ! grep -qF 'references/CLAUDE.md' "$root_claude"; then
  printf '\n%s\n' "$pointer_line" >> "$root_claude"
fi

printf 'wiki scaffolded at: %s\n' "$project_root/references"
