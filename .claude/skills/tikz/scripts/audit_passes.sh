#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
  echo "Usage: audit_passes.sh <file.tex> [--compile]" >&2
  exit 2
fi

tex_file="$1"
mode="${2:-}"

if [ ! -f "$tex_file" ]; then
  echo "File not found: $tex_file" >&2
  exit 1
fi

run_grep() {
  local label="$1"
  local pattern="$2"

  printf '\n## %s\n' "$label"
  grep -nE "$pattern" "$tex_file" || true
}

run_filtered_grep() {
  local label="$1"
  local include_pattern="$2"
  local exclude_pattern="$3"

  printf '\n## %s\n' "$label"
  grep -nE "$include_pattern" "$tex_file" | grep -vE "$exclude_pattern" || true
}

printf '# TikZ Audit Pass Inputs: %s\n' "$tex_file"

run_grep "Scope: frames, tikzpictures, nodes, draws, bends, loops" 'tikzpicture|begin\{frame\}|node|draw|bend|foreach'
run_filtered_grep "Autosized node candidates" '\\node' 'minimum'
run_grep "Scale usage" 'scale='
run_grep "Coordinate map comments" '% Coordinate map|% Node map|% Layout'
run_filtered_grep "Pass 0 candidates: node declarations" 'node.*\{' '^[[:space:]]*%'
run_grep "Pass 1 candidates: Bezier bends" 'bend'
printf '\n## Pass 3 candidates: arrow labels missing directional keywords\n'
perl -ne 'print "$.:" . $_ if /node(?:\[(?![^\]]*(?:above|below|left|right|anchor|pos|midway|near))[^\]]*\])?\s*\{/' "$tex_file" || true

printf '\n## TikZ picture count\n'
grep -c 'begin{tikzpicture}' "$tex_file" || true

if [ "$mode" = "--compile" ]; then
  printf '\n## Compile warnings\n'
  work_dir="$(cd "$(dirname "$tex_file")" && pwd)"
  base_name="$(basename "$tex_file")"
  (
    cd "$work_dir"
    pdflatex -interaction=nonstopmode "$base_name" 2>&1 \
      | grep -E 'Overfull|Underfull|Error|Warning' || true
  )
elif [ -n "$mode" ]; then
  echo "Unknown mode: $mode" >&2
  exit 2
fi
