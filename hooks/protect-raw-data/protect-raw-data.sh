#!/usr/bin/env bash
# PreToolUse hook. protect-raw-data — the FAST TOP-LAYER EXPLANATION, not the guarantee.
#
# It denies a direct Write/Edit/MultiEdit/NotebookEdit whose resolved path lands inside
# <project>/data/raw, and hands Claude a sentence telling it to write to data/clean instead.
# It resolves symlinks and ".." in the parent path and compares case-insensitively, so the
# symlinked-parent / case-variant / traversal evasions do not slip past it.
#
# WHAT THIS HOOK DELIBERATELY DOES NOT DO (learned from red-teaming, per S. Cunningham's
# Substack + the Andy Wheeler critique):
#   - It does NOT guard Bash or scan script bodies. A child process (Rscript clean.R,
#     python3 x.py) writes via syscalls this hook never sees ("not in the room"), and
#     textual matching of commands is defeatable by construction and throws false positives.
#   - Therefore this hook is NOT the wall. The wall is the kernel seal (root:wheel, dir 555 /
#     files 444; see gtd/scripts/seal_raw.sh) plus the mechanism-agnostic SHA-256 manifest
#     check that gates every pipeline run (gtd/scripts/raw_manifest.py --check).
#   - It FAILS OPEN: any internal error allows the action rather than freezing the workspace.
set -uo pipefail

# Fail open on any unexpected error.
trap 'exit 0' ERR

payload="$(cat)"
tool="$(printf '%s' "$payload" | jq -r '.tool_name // empty' 2>/dev/null)"
case "$tool" in
  Write|Edit|MultiEdit|NotebookEdit) ;;
  *) exit 0 ;;
esac

f="$(printf '%s' "$payload" | jq -r '.tool_input.file_path // .tool_input.notebook_path // empty' 2>/dev/null)"
[ -z "$f" ] && exit 0

# Project root: Claude Code sets CLAUDE_PROJECT_DIR; fall back to the payload cwd, then PWD.
proj="${CLAUDE_PROJECT_DIR:-}"
[ -z "$proj" ] && proj="$(printf '%s' "$payload" | jq -r '.cwd // empty' 2>/dev/null)"
[ -z "$proj" ] && proj="$PWD"

# The one immutable place. If it does not exist, there is nothing to protect.
raw="$proj/data/raw"
[ -d "$raw" ] || exit 0
raw_real="$(cd "$raw" 2>/dev/null && pwd -P)" || exit 0

# Lifecycle gate: immutability is a PHASE, not a constant. Raw is written ONCE during acquisition
# (scraping, downloading, importing originals) and only THEN frozen. The freeze is signalled by
# the baseline manifest. Before it exists, raw is still being filled — allow writes so acquisition
# is not forced into workarounds (which is how research files end up split between raw and clean).
# After `raw_manifest.py write` creates the baseline, raw is frozen and the hook guards it.
[ -f "$proj/data/.raw_manifest.sha256" ] || exit 0

# Textually collapse "." and ".." in an absolute path (base is already physical, so this is safe).
normalize() {
  local seg; local -a out=()
  local IFS=/; read -ra segs <<< "$1"
  for seg in "${segs[@]}"; do
    case "$seg" in
      ''|.) ;;
      ..) [ ${#out[@]} -gt 0 ] && unset 'out[${#out[@]}-1]' ;;
      *) out+=("$seg") ;;
    esac
  done
  printf '/%s' "${out[@]}"
}

# Resolve the target's parent to a PHYSICAL path even when it does not exist yet (Write auto-
# creates parent dirs, so a not-yet-existent path under raw must still be blocked — the old
# "cd || exit 0" fail-open let data/raw/newsub/x.csv slip past). Walk up to the nearest existing
# ancestor, resolve THAT with pwd -P (collapsing symlinks), then re-attach the missing segments
# and collapse "." / ".." textually.
case "$f" in /*) abs="$f" ;; *) abs="$proj/$f" ;; esac
d="$(dirname "$abs")"; missing=""
while [ -n "$d" ] && [ "$d" != "/" ] && [ "$d" != "." ] && [ ! -d "$d" ]; do
  missing="$(basename "$d")/$missing"; d="$(dirname "$d")"
done
base="$(cd "$d" 2>/dev/null && pwd -P)" || exit 0
tgt="$(normalize "$base/$missing$(basename "$abs")")"

# Case-insensitive containment test (macOS APFS is case-insensitive by default).
lc() { printf '%s' "$1" | tr '[:upper:]' '[:lower:]'; }
if [ "$(lc "$tgt/")" = "$(lc "$raw_real/")" ] || case "$(lc "$tgt")" in "$(lc "$raw_real")"/*) true ;; *) false ;; esac; then
  {
    echo "protect-raw-data: refusing to $tool a file inside data/raw."
    echo "  target resolves to: $tgt"
    echo "  raw (immutable):    $raw_real"
    echo "The original data must stay byte-identical. Read it freely, but write any derived"
    echo "output to data/clean/ instead. (This hook is the explanation; the kernel seal and the"
    echo "SHA-256 manifest are the actual guarantee.)"
  } >&2
  exit 2
fi
exit 0
