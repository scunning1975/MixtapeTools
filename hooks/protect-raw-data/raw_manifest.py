#!/usr/bin/env python3
"""raw_manifest — the mechanism-agnostic guarantee that data/raw is byte-identical.

Unlike a hook (which only sees tool arguments) or a permission bit (which only stops some
verbs), a content hash catches ANY change to the raw data no matter how it arrived: a Write,
an Edit, an R or Python child process, a rename, a delete-then-recreate. It does not care who
did it or how. That is the point.

Usage (run from the project root, or pass --raw / --manifest):
    raw_manifest.py write     # baseline: hash every file in data/raw, save the manifest
    raw_manifest.py check     # GATE: recompute and compare. Exit 1 (fail-CLOSED) on any change.

Put `raw_manifest.py check` as step 0 of your pipeline, BEFORE anything reads the data. A check
that runs after the read is forensics, not protection.

The manifest itself (data/.raw_manifest.sha256) should be protected too — ideally root-owned
alongside the kernel seal (see seal_raw.sh), so an over-eager agent cannot rewrite its own
detector to pass.
"""
import argparse
import hashlib
import os
import sys

DEFAULT_RAW = "data/raw"
DEFAULT_MANIFEST = "data/.raw_manifest.sha256"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def scan(raw):
    """Return ({relpath: sha256}, [symlink relpaths]) for every entry under raw, sorted.

    Symlinks are NOT hashed and NOT followed. A symlink inside data/raw is a content channel
    the hash cannot see (its target's bytes can change while the link path stays the same), so
    raw_manifest REFUSES any symlink in the vault rather than pretend to certify it. Raw data
    must be regular files only. (Closes the red-team's symlink-content breach, Tom #11 / Dick C1.)
    """
    files, links = {}, []
    for dirpath, dirnames, filenames in os.walk(raw, followlinks=False):
        for name in dirnames + filenames:
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, raw)
            if os.path.islink(full):
                links.append(rel)
            elif os.path.isfile(full):
                files[rel] = sha256(full)
    return dict(sorted(files.items())), sorted(links)


def _root_of(files):
    return hashlib.sha256("".join(f"{h}  {r}\n" for r, h in files.items()).encode()).hexdigest()


def load(manifest):
    """Return ({relpath: sha256}, stored_root_or_None)."""
    m, root = {}, None
    with open(manifest) as fh:
        for line in fh:
            line = line.rstrip("\n")
            if line.startswith("# root "):
                root = line[len("# root "):].strip()
            elif not line or line.startswith("#"):
                continue
            else:
                digest, rel = line.split("  ", 1)
                m[rel] = digest
    return m, root


def write(raw, manifest):
    if not os.path.isdir(raw):
        sys.exit(f"raw_manifest: {raw} does not exist; nothing to baseline.")
    files, links = scan(raw)
    if links:
        sys.exit("raw_manifest: REFUSING to baseline — data/raw contains symlink(s):\n"
                 + "\n".join(f"  {rel}" for rel in links)
                 + "\nRaw data must be regular files only (a symlink is an unmonitored content "
                   "channel). Replace the symlink(s) with real files, then re-run.")
    root = _root_of(files)
    os.makedirs(os.path.dirname(manifest) or ".", exist_ok=True)
    with open(manifest, "w") as fh:
        fh.write(f"# raw_manifest v1 — {len(files)} files under {raw}\n")
        fh.write(f"# root {root}\n")
        for rel, h in files.items():
            fh.write(f"{h}  {rel}\n")
    print(f"wrote {manifest}: {len(files)} files, root {root[:16]}…")


def check(raw, manifest):
    if not os.path.isfile(manifest):
        sys.exit(f"raw_manifest: no manifest at {manifest}. Run `write` to baseline first.")
    if not os.path.isdir(raw):
        print(f"FAIL: the raw vault {raw} is GONE (renamed or deleted).", file=sys.stderr)
        sys.exit(1)
    expected, stored_root = load(manifest)
    # The manifest must be internally consistent: recomputing the root over its own file lines
    # must equal the stored root. Catches a partial hand-edit of the manifest (Harry #4).
    if stored_root is not None and _root_of(expected) != stored_root:
        print("FAIL: the manifest is internally inconsistent (its file lines do not match its "
              "own root fingerprint). It has been tampered with.", file=sys.stderr)
        sys.exit(1)
    actual, links = scan(raw)
    if links:
        print("FAIL: data/raw contains symlink(s), which are forbidden (unmonitored content "
              "channel):\n" + "\n".join(f"  {rel}" for rel in links), file=sys.stderr)
        sys.exit(1)
    problems = []
    for rel, h in expected.items():
        if rel not in actual:
            problems.append(f"  MISSING   {rel}")
        elif actual[rel] != h:
            problems.append(f"  CHANGED   {rel}")
    for rel in actual:
        if rel not in expected:
            problems.append(f"  NEW FILE  {rel}")
    if problems:
        print(f"FAIL: data/raw does not match the manifest ({len(problems)} discrepancies):",
              file=sys.stderr)
        print("\n".join(problems), file=sys.stderr)
        print("\nThe raw data changed since it was sealed. Refusing to certify. "
              "Restore from backup (L0) or investigate before any run reads it.", file=sys.stderr)
        sys.exit(1)
    print(f"OK: data/raw matches the manifest ({len(expected)} files unchanged).")


def main():
    ap = argparse.ArgumentParser(description="Hash-verify data/raw is byte-identical.")
    ap.add_argument("action", choices=["write", "check"])
    ap.add_argument("--raw", default=DEFAULT_RAW)
    ap.add_argument("--manifest", default=DEFAULT_MANIFEST)
    a = ap.parse_args()
    (write if a.action == "write" else check)(a.raw, a.manifest)


if __name__ == "__main__":
    main()
