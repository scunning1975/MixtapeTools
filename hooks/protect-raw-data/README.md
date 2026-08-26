# protect-raw-data

The raw data cannot change. Not by you, not by an agent, not by accident. This is the first
hook in MixtapeTools, and it is really three layers, because a hook alone cannot do the job.

The story behind it is in the Substack posts "How and why I am using hooks" parts 1 and 2. Short
version: a hook only sees the arguments handed to a tool, so an R or Python script the agent
writes and runs can edit a raw file underneath it. Andy Wheeler pointed this out. The fix is not
a bigger hook. It is a stack.

## The three layers

1. **The hook** (`protect-raw-data.sh`) — a Claude Code PreToolUse hook. Blocks a direct
   Write/Edit/MultiEdit/NotebookEdit into `data/raw`, and tells the agent to write to
   `data/clean` instead. It resolves shortcuts, `..`, and capital-letter path tricks, and it
   fails open (if the hook breaks, it lets you through rather than freezing you out). It is the
   fast, friendly note that catches the honest mistake. It is NOT the guarantee.

2. **The lock** (`seal_raw.sh`) — the kernel wall. Hands `data/raw` (and the manifest and these
   guard scripts) to `root:wheel`, read-only. Now an agent running as you cannot overwrite,
   delete, or unlock a raw file without your password. This is the actual guarantee, and it is
   the one thing here that needs `sudo`.

3. **The fingerprint** (`raw_manifest.py` + `check_raw.sh`) — a SHA-256 of every raw file, saved
   once. `check_raw.sh` compares it at the start of every run and stops cold if anything changed,
   by any tool, script, or rename. It does not care how the file changed, so it has no door to
   walk around. Run it as step 0 of your pipeline.

## Assumptions

You keep original data in `data/raw` and derived data in `data/clean`. That folder layout is
what the hook keys off.

## Setup

The hook is user-level. Register it once in `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Write|Edit|MultiEdit|NotebookEdit",
        "hooks": [ { "type": "command", "command": "$HOME/.claude/hooks/protect-raw-data.sh", "timeout": 10 } ] }
    ]
  }
}
```
Copy `protect-raw-data.sh` to `~/.claude/hooks/` and `chmod +x` it. Copy the other three scripts
into your project's `scripts/` folder.

## Using it (the lifecycle matters)

Being unchangeable is a phase, not a permanent state. You have to load data in before you freeze
it. So the hook only starts guarding once you take the fingerprint.

```bash
# 1. Put your original data in data/raw (scrape, download, import). Raw is still open.

# 2. Freeze it: take the fingerprint. From now on the hook guards data/raw.
python3 scripts/raw_manifest.py write

# 3. Lock it (needs your password). Makes it immutable at the kernel, and locks the
#    fingerprint and these scripts too, so an agent can't forge its own report card.
sudo bash scripts/seal_raw.sh "$PWD"

# 4. Gate every pipeline run. Make this the first thing your pipeline does:
bash scripts/check_raw.sh "$PWD"   # exits 1 and refuses to continue if raw changed
```

To legitimately update raw data later:

```bash
sudo bash scripts/seal_raw.sh --unseal "$PWD"   # give it back to yourself
# ... add or replace files ...
python3 scripts/raw_manifest.py write           # re-take the fingerprint
sudo bash scripts/seal_raw.sh "$PWD"            # re-lock
```

## What it does not do

- It does not protect files reachable only through a shortcut (symlink) inside `data/raw`;
  `raw_manifest.py` refuses to certify if a symlink is present, so keep raw as real files.
- The lock is local to one machine (cloud sync does not carry file ownership across machines),
  so re-run `seal_raw.sh` on each machine you work from.
- Renaming the whole project folder is still possible. That is a loud, recoverable annoyance,
  not a silent change: the fingerprint check sees the vault is gone and refuses to certify.

## Notes

- macOS. The lock uses `root:wheel` ownership; on macOS you can add an extra belt with
  `sudo chflags -R schg data/raw`.
- Tested by three red-team agents attacking a sandboxed vault, then re-tested on a real
  cloud-synced project. Every attack that beat an earlier version is closed.
