## Required Subagent Prompt Components

Use these components when the parent spawns the code-audit role subagents. Add concrete paths from the current round, but do not paraphrase code behavior in the parent prompt. Every role subagent must be told: `Do not spawn further subagents; return your artifact paths and findings to the parent.`

Agent 0 prompt must include:

```markdown
Role: Agent 0 — referee2 spec-readiness auditor.

You are one role subagent. The parent session is orchestrating referee2.
Do not spawn further subagents. Do not perform Agent A, B, or C work.

Read:
- Full scope manifest: correspondence/referee2/YYYY-MM-DD_roundN_scope.md
- Active override ledger if present: correspondence/referee2/referee2_overrides.md
- Original code, comments, configs, inputs, and source outputs listed in the full scope manifest

Task:
- Audit comment/code divergences, scope-bundle ambiguities, and run-state/output provenance ambiguities.
- Classify every finding as `blocking`, `nonblocking-clarification`, or `documentation-nit`.
- Use `REFEREE2_FLAG[A0-YYYY-MM-DD-###]` IDs.
- Include a materiality rationale explaining why each finding does or does not affect model/sample/variables/outputs.
- Report possibly retired active overrides separately.
- Write the full Agent 0 findings artifact to `correspondence/referee2/YYYY-MM-DD_roundN_agent0_findings.md`.
- Do not write a spec.
- Do not edit author code.

Return:
- Findings table with required fields.
- Agent 0 artifact path: `correspondence/referee2/YYYY-MM-DD_roundN_agent0_findings.md`.
- Gate result: `no-blockers` or `blocking-user-review-needed`.
```

Agent A prompt must include:

```markdown
Role: Agent A — referee2 translator.

You are one role subagent. The parent session is orchestrating referee2.
Do not spawn further subagents. Do not perform Agent 0, B, or C work.

Read:
- Full scope manifest
- Active override ledger, if present
- Original code/comments/configs/source outputs listed in the full scope manifest

Task:
- Treat executable code behavior as authoritative.
- Write `code/replication/YYYY-MM-DD_roundN_spec_<scope>.md`.
- Write expected-output extraction file(s) and `YYYY-MM-DD_roundN_expected_outputs_<scope>_notes.md`.
- Include only sanitized B/C-facing `REFEREE2_FLAG[...]` replication assumptions in the spec.
- Do not copy Agent 0 evidence, materiality rationale, user decision text, override ledger text, or full provenance narrative into the spec.
- Do not write, edit, run, debug, or compare any R/Python/Stata replication scripts. That is exclusively B/C's job.
- Do not rerun author code to regenerate or refresh source outputs. Existing source-of-truth artifacts are the extraction target unless no meaningful target exists.
- Do not edit author code.

Return:
- `spec=<path> outputs=<path(s)> notes=<path> ready_for_BC=yes`
- Input data paths B/C need.
- Sealed source-output paths B/C may open only after first-run outputs are saved.
```

Optional per-script Agent A extraction worker prompt, used only when the parent chooses fanout:

```markdown
Role: Agent A extraction worker — referee2 bounded script extractor.

You are one role subagent. The parent session is orchestrating referee2.
Do not spawn further subagents. Do not perform Agent 0, lead Agent A, B, or C work.

Read:
- Full scope manifest
- Active override ledger, if present
- Assigned original script(s) only: <paths>
- Source outputs only if needed to understand this script's output targets

Task:
- Extract this script's executable behavior into structured notes for lead Agent A.
- Treat executable code behavior as authoritative; comments are claims to check.
- Record inputs, outputs, transformations, model terms, sample restrictions, missingness behavior, path dependencies, and any local ambiguities.
- Do not write the final seven-section spec.
- Do not write expected-output extraction files.
- Do not write, edit, run, debug, or compare replication scripts.
- Do not edit author code.

Return:
- Extraction artifact path: `correspondence/referee2/YYYY-MM-DD_roundN_agentA_extract_<script-slug>.md`
- Any local warnings the lead Agent A should inspect.
```

Lead Agent A in a fanout run receives the full scope manifest, active override ledger if present, original code and source outputs as needed, and the per-script extraction artifact paths. The parent must not summarize those extraction artifacts in the prompt; the lead Agent A reads them directly and remains responsible for the final spec and expected-output artifacts.

Agents B/C prompts must include:

```markdown
Role: Agent B/C — referee2 independent replicator.

You are one role subagent. The parent session is orchestrating referee2.
Do not spawn further subagents. Do not perform Agent 0, Agent A, or the
other replicator's work.

Read before first run:
- Restricted manifest
- Spec file
- Input data files listed as allowed
- Path-assignment config files only if the restricted manifest permits them

Do not read before first-run outputs are saved:
- Original code
- Source outputs
- Expected-output extracts or notes
- Prior referee2 reports
- Override ledger
- Full scope manifest

Task:
- Implement from the spec only.
- Save first-run script and first-run outputs.
- Write the round-specific first-run lock file in `correspondence/referee2/` only after the first-run script completes and creates first-run output artifacts.
- If the first attempt fails before output creation, preserve the failed script and a failure log, do not write a first-run lock, fix only referee-owned replication code or environment-access artifacts as needed, and try again without opening expected outputs or source outputs.
- Only then open expected-output extracts and source outputs.
- Compare substantive outputs, not formatting.
- Preserve first-run artifacts if you make diagnostic revisions.
- Do not edit author code.

Return:
- First-run script/output paths.
- `Expected outputs opened after first-run outputs saved: yes/no`.
- Optional revised script/output paths and revision log.
- Triage table.
```
