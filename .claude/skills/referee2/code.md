# Referee 2 Code Mode

This file is the code-audit mode index. Read `referee2.md` first for shared persona, scope calibration, audit categories, and report expectations. Then load only the code-mode files needed for the current phase or role.

## Progressive Disclosure

For parent orchestration, read these files in order:

1. `code_tainted_session.md` — independence check, tainted-session catch, model overrides, path enumeration, and re-invocation rules.
2. `code_protocol.md` — code-mode boundary, four-agent architecture, round protocol, Agent 0 materiality gate, and override ledger.
3. `code_subagent_prompts.md` — role prompt components for Agent 0, Agent A, optional Agent A extraction workers, and Agents B/C.
4. `code_spec_outputs.md` — spec template, comment handling, expected-output extraction, sealed targets, first-run locks, and figure targets.
5. `code_reporting.md` — discrepancy triage, final audit outputs, tainted-session operationalization, report format, and file locations.

For role subagents, load the narrowest set that covers the assigned role:

| Role | Required files |
|---|---|
| Agent 0 | `referee2.md`, `code_protocol.md`, `code_subagent_prompts.md` |
| Agent A | `referee2.md`, `code_protocol.md`, `code_subagent_prompts.md`, `code_spec_outputs.md` |
| Agent A extraction worker | `referee2.md`, `code_subagent_prompts.md`, `code_spec_outputs.md` |
| Agent B/C | `referee2.md`, `code_subagent_prompts.md`, `code_spec_outputs.md`, `code_reporting.md` |
| Parent final report aggregation | `referee2.md`, `code_reporting.md` |

If unsure which phase applies, read the files in the parent-orchestration order above. Do not skip `code_tainted_session.md` before any code audit work in the parent session.

## Files

- `code_tainted_session.md`
- `code_protocol.md`
- `code_subagent_prompts.md`
- `code_spec_outputs.md`
- `code_reporting.md`
