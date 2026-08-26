#!/usr/bin/env bash
# seal_raw — the KERNEL WALL that actually makes data/raw immutable to a non-root agent.
#
# A hook only sees tool arguments; a 444 bit on a user-owned file in a user-owned directory is
# defeated by delete-then-recreate (unlink is a DIRECTORY permission) and by `chmod u+w` (the
# user owns the file). The only thing an agent running as you CANNOT do without your password is
# touch a tree owned by root. So we give the vault to root:wheel and make it read+traverse-only.
#
#   dir  data/raw     -> root:wheel, 555 (r-xr-xr-x): readable + enterable, NOT writable
#   files inside      -> root:wheel, 444 (r--r--r--): readable, NOT writable, NOT deletable
#                        (deletion needs write on the dir, which only root now has)
#
# After this, an agent running as you gets EACCES/EPERM on: in-place write, truncate,
# delete-then-recreate, chmod-unseal (not the owner). Reads still work — the whole point.
#
# THIS REQUIRES YOUR PASSWORD. Run it yourself:   sudo bash seal_raw.sh [PROJECT_DIR]
# To make legitimate changes to raw later:        sudo bash seal_raw.sh --unseal [PROJECT_DIR]
#   ...then add/replace files, re-baseline the manifest (raw_manifest.py write), then re-seal.
set -euo pipefail

mode="seal"
if [ "${1:-}" = "--unseal" ]; then mode="unseal"; shift; fi
proj="${1:-$PWD}"
raw="$proj/data/raw"
mani="$proj/data/.raw_manifest.sha256"
# The detector must be sealed too, or an agent forges the manifest / patches the checker to pass
# (red-team Harry/Dick). Root-own the manifest and the guard scripts alongside the vault.
guards=("$mani" "$proj/scripts/raw_manifest.py" "$proj/scripts/check_raw.sh")

[ -d "$raw" ] || { echo "seal_raw: $raw does not exist." >&2; exit 1; }
if [ "$(id -u)" -ne 0 ]; then
  echo "seal_raw: must run as root. Re-run:  sudo bash $0 ${mode/seal/}${mode/unseal/--unseal} \"$proj\"" >&2
  echo "  (seal:   sudo bash $0 \"$proj\")" >&2
  echo "  (unseal: sudo bash $0 --unseal \"$proj\")" >&2
  exit 1
fi

owner="${SUDO_USER:-$(logname)}"
if [ "$mode" = "unseal" ]; then
  # Return the vault AND the manifest to you so you can update + re-baseline. Re-seal afterward.
  chown -R "$owner":staff "$raw"
  chmod -R u+w "$raw"
  find "$raw" -type d -exec chmod 755 {} \;
  find "$raw" -type f -exec chmod 644 {} \;
  [ -f "$mani" ] && { chown "$owner":staff "$mani"; chmod 644 "$mani"; }
  echo "UNSEALED: $raw and its manifest are writable by you again."
  echo "  Now update the files, then:  python3 scripts/raw_manifest.py write"
  echo "  Then RE-SEAL:                 sudo bash $0 \"$proj\""
  exit 0
fi

# Seal the vault.
chown -R root:wheel "$raw"
find "$raw" -type d -exec chmod 555 {} \;
find "$raw" -type f -exec chmod 444 {} \;
# Seal the detector (manifest + guard scripts), so it cannot be forged or patched.
for g in "${guards[@]}"; do
  [ -f "$g" ] && { chown root:wheel "$g"; chmod 444 "$g"; }
done
echo "SEALED: $raw is now root:wheel, dirs 555 / files 444."
echo "        the manifest and guard scripts are root:wheel 444 (cannot be forged or patched)."
echo "  You (and the agent) can read raw but cannot write, delete, or chmod it without sudo."
echo "  Verify the guarantee (trusted invocation):  bash scripts/check_raw.sh \"$proj\""
echo "  (Optional extra lock on macOS:  sudo chflags -R schg \"$raw\"  — even root can't clear at securelevel>0)"
