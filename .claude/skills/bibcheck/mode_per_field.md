# Per-field mode

One CLI subprocess per field. Each specialist reads the whole bibliography but checks only its field. The point of this mode is **isolation**: each specialist agent should not see what the others are concluding. Launching each as a separate `claude -p` subprocess gives a fresh CLI session with no shared conversation memory.

See `methodology.md` for why per-field mode requires CLI isolation rather than in-conversation subagents.

## Step 3b.1 — Build and launch one specialist per field

For each field in the list `[title, year, journal, authors, volume_issue, pages, doi]`:

1. Build a prompt for the specialist that contains:
   - The full `input.bib` content
   - The field name
   - Instructions: "For each entry in this .bib, check ONLY the {field}. Compare against the canonical paper found via WebSearch. Output JSON to stdout: a list of {key, status, original, corrected, reason}."

2. Launch the specialist via Bash:

   ```bash
   claude --dangerously-skip-permissions -p "<the specialist prompt>" > reports/field_<field>.json 2>reports/field_<field>.log
   ```

3. Run subprocesses in parallel up to `--max-parallel`. Wait for all to complete.

## Step 3b.2 — Final reviewer pass

A consolidator agent reads all `field_*.json`, joins by entry key, and produces:

- `bibcheck_report.md` — disagreements across specialists are flagged (e.g., title-specialist says X, year-specialist disagrees about which paper is being cited).
- `corrected.bib` — applies a field-level fix only if the relevant specialist flagged it AND the cross-field consensus supports the fix.
