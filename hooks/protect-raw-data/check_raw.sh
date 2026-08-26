#!/usr/bin/env bash
# check_raw.sh — the TRUSTED invocation of the raw-data gate. Make this step 0 of the pipeline.
#
# Running raw_manifest.py directly is defeatable by attacking the INVOCATION: a decoy python3
# earlier on PATH, a PYTHONPATH that shadows hashlib, or decoy --raw/--manifest paths (red-team
# Harry #5/#7a/#7b). This wrapper removes that surface:
#   - pins an absolute, trusted interpreter (the system python; raw_manifest.py is stdlib-only)
#   - runs under a sanitized environment (env -i, fixed PATH) so PATH/PYTHONPATH tricks die
#   - hardcodes the sealed absolute paths so a decoy cannot be substituted
#
# For a real guarantee this wrapper AND raw_manifest.py AND the manifest should be root-owned and
# sealed (see seal_raw.sh), so an agent cannot edit the gate it is about to run.
set -euo pipefail
proj="${1:-$PWD}"

PY="/usr/bin/python3"                       # macOS always ships this; stdlib is complete
[ -x "$PY" ] || PY="$(command -v python3 || true)"
[ -n "$PY" ] && [ -x "$PY" ] || { echo "check_raw: no usable python3 found" >&2; exit 1; }

exec env -i PATH=/usr/bin:/bin HOME="$HOME" \
  "$PY" "$proj/scripts/raw_manifest.py" check \
  --raw "$proj/data/raw" \
  --manifest "$proj/data/.raw_manifest.sha256"
