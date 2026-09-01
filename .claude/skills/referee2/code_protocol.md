## Mode 2: Code Audit

### Non-Negotiable Boundary: Never Edit Author Code

Referee2 may write only its own audit artifacts:

- scope manifests
- override ledgers
- plain-language specs
- expected-output extraction files and notes
- replication scripts
- first-run and revised replication outputs
- referee reports

Referee2 must never edit author code, comments, data-cleaning scripts, analysis scripts, project documentation, or source output artifacts. This remains true even if the user asks for fixes during the referee2 interaction. If the user wants fixes, stop the audit, run a normal coding session or feature branch outside referee2, then rerun referee2.

Agent A treats current executable code behavior as authoritative. Comments help with labels and interpretation, but comments never override code behavior. If the user decides a comment reflects intent and code is wrong, stop the audit until author code is fixed outside referee2. Agent A is a translator/extractor only: it never writes, runs, debugs, or compares replication scripts.

### The Core Principle: Cross-Language Replication

Hallucination errors in LLM-generated code are like measurement error. If Claude writes buggy R code, the same Claude writing Stata code will likely make a *different* bug. These errors are **orthogonal across languages**.

Cross-language replication exploits this orthogonality:
1. **Write a specification first** (see "Specification bottleneck" below) — this is what protects orthogonality
2. Implement the replication in another language **from the spec, not from the original code**
3. Select outputs wisely — specific numerical values that should be identical
4. Compare to 6+ decimal places
5. Where results differ, **classify and diagnose** per the triage table below

### The Specification Bottleneck

**Why this exists.** If the auditor reads the original code (comments and all) and translates line-by-line into another language, the orthogonality argument collapses — the new code reproduces the same conceptual mistakes in different syntax, and the bug survives translation. The spec bottleneck forces compression through a verbal layer where ambiguities surface and where independent implementation can re-derive the structure.

**Why telling one agent to "set the original code aside" doesn't work.** Context cannot be unread. A single Claude that sees the original code and then writes the spec and then writes the replication is implementing from-the-code, not from-the-spec — the spec becomes a side channel while the original code drives the translation. To enforce the bottleneck, the agent that reads the original code and the agents that write the replications must be **separate subagents with isolated contexts**.

**If a handoff cannot happen, stop at the missing stage.** Agent A writing B/C's R, Python, or Stata scripts invalidates the cross-language replication. Agent 0 writing Agent A's spec is also invalid. If the parent cannot spawn the next required isolated role subagent, do not continue in the same context. Preserve completed artifacts, report `Status: partial-audit-replication-blocked`, and allow a later invocation to resume at the next missing role if source state is unchanged.

**Four-agent architecture:**

| Agent | Reads | Produces |
|---|---|---|
| **0 — Auditor** | Full scope manifest, active override ledger, original code + comments, source outputs for provenance | Materiality-tiered readiness findings only. Does NOT write a spec. |
| **A — Translator** | Original code + comments, full scope manifest, active override ledger, source-of-truth outputs | Spec file + expected-output extraction files and notes. |
| **B — Replicator (language 1)** | Restricted manifest, spec, input data, path-assignment config only. Expected outputs and source outputs are sealed until first-run artifacts are saved. **Never sees the original code.** | First-run replication script/output, optional revised script/output, comparison table. |
| **C — Replicator (language 2)** | Same as B; never sees original code. | First-run replication script/output, optional revised script/output, comparison table. |

The parent session orchestrates by spawning role subagents and aggregating their reports. **The parent does not perform the role work.** It may create manifests, pass artifact paths, wait for subagent results, present blocking menus, and write the final report from role-subagent outputs. It must not read original code to audit it, write Agent A's spec, or write B/C replication scripts. **The parent does not read spec content** — it only passes file paths to B and C. The parent's own context is contaminated (it has the user's invocation and Step -1's enumeration); if it summarizes the spec into B/C's prompts, that contaminated paraphrase replaces the clean spec. Hand off via `Read these files before doing anything: <restricted manifest path>, <spec path>, <input data paths>` and let B/C read the files themselves. If a role subagent cannot be spawned, the parent must not ask the previous role or itself to "just do the next step."

**Why split Agent 0 from Agent A.** A single agent that does "audit, and if clean write the spec" judges its own gate. Splitting prevents Agent 0's comment/code read from becoming the spec-writing voice. Agent 0 gates only material blockers; nonblocking clarifications and documentation nits proceed as flagged audit state.

**The protocol:**

1. **Discover and confirm the scope bundle.** Default to the audited entrypoint(s), sourced/imported code, configs, required inputs, and source-of-truth output artifacts. If the user explicitly narrows scope, honor that guardrail and record it.
2. **Check for resumable artifacts.** Before creating a new round, check whether the newest incomplete round for the same scope can resume:
   - Agent 0 findings exist with no blocking issues, but no matching Agent A spec exists: ask whether to resume at Agent A.
   - Agent A spec, expected-output artifacts, expected-output notes, and restricted manifest exist, but matching B/C comparison artifacts are missing: ask whether to resume at B/C.
   Resume only if the source files and source-output artifacts listed in that round's full scope manifest are unchanged since the last completed stage artifact was written. If anything changed, start a new round from Agent 0.
3. **Write the full scope manifest for a new round.** If not resuming, create `correspondence/referee2/YYYY-MM-DD_roundN_scope.md`. Infer `roundN` by scanning existing `correspondence/referee2/YYYY-MM-DD_round*_*.md` files for today's date and taking max `N + 1`; if none exist, use `round1`. Include enough source-state information to support later resume checks: at minimum path, file size, and modified time for original code/config/source-output artifacts, and hashes where feasible.
4. **Read active overrides.** If `correspondence/referee2/referee2_overrides.md` exists, read only entries with `Status: active`. If it does not exist, create it lazily only when the first override is needed.
5. **Spawn Agent 0 (auditor).** Prompt: audit full spec-readiness across comment/code divergences, scope-bundle ambiguities, and run-state/output provenance ambiguities. Return materiality-tiered findings. Do NOT write a spec.
6. **Gate only on material blockers.** If Agent 0 finds `blocking` issues not covered by active overrides, stop for user review and follow the blocking menu below. If Agent 0 finds only `nonblocking-clarification` or `documentation-nit` issues, proceed automatically and carry relevant `REFEREE2_FLAG[...]` assumptions into Agent A.
7. **Spawn Agent A (translator).** Prompt: read the source code and source-of-truth outputs, treat executable code behavior as authoritative, and write the spec to `code/replication/YYYY-MM-DD_roundN_spec_<scope>.md`, expected-output extraction files, and `YYYY-MM-DD_roundN_expected_outputs_<scope>_notes.md`. Agent A stops after writing these artifacts and returns a one-line status: `spec=<path> outputs=<path> notes=<path> restricted_manifest_needed=yes ready_for_BC=yes`. For large multi-script projects, the parent may first spawn bounded per-script Agent A extraction workers and then give their artifact paths to the lead Agent A. The parent, not any subagent, decides whether to use this fanout.
8. **Write the restricted B/C manifest.** Create `correspondence/referee2/YYYY-MM-DD_roundN_restricted_manifest.md` listing allowed pre-first-run files, sealed target paths, and prohibited files.
9. **Verify B/C handoff availability.** Before beginning cross-language replication, confirm that B and C can run as separate isolated subagents. If they cannot, stop with `Status: partial-audit-replication-blocked`; keep the Agent A artifacts for a later resume at B/C.
10. **Spawn Agents B and C.** Each receives the restricted manifest, spec path, and input data paths. Each writes and runs a first-run replication before opening expected outputs or source outputs. Each compares after first-run artifacts are saved, may make diagnostic revisions, and returns a triage table. If Agent A was fanned out by script or script group, fan out B/C on the same units so every extraction unit gets one B-language replication and one C-language replication. Run fanout units sequentially by default; run same-stage units in parallel only when the user supplied `--parallel`.
11. **Run output automation check only if user requested it.** If and only if the user explicitly asked referee2 to check output automation/rerun reproducibility, the parent may run the original entrypoint and compare generated source artifacts to the pre-existing source-of-truth outputs. This is parent-owned diagnostic evidence and is separate from Agent A's expected-output extraction.
12. **Aggregate.** The parent collects B's and C's triage tables, combines them with the other audits, and files the formal report. The triage table format and discrepancy categories are defined further down.

### Agent 0 Materiality Tiers

Agent 0 does not use a binary clean/dirty gate. It classifies each finding into one of three tiers:

| Tier | Meaning | Gate effect |
|---|---|---|
| `blocking` | A reasonable replication could produce different scientific conclusions depending on whether code, comments, scope, or output provenance are treated as authoritative. | Stops Agent A unless covered by an active override. |
| `nonblocking-clarification` | A mismatch or ambiguity exists, but Agent 0 can state why it is unlikely to affect the model, sample, variables, or reported outputs. | Proceeds to Agent A with a `REFEREE2_FLAG[...]` assumption where relevant. |
| `documentation-nit` | Documentation is stale, vague, or stylistically misleading, but no replication-relevant ambiguity remains. | Proceeds; report in Agent 0/final report only. |

Usually classify as `blocking` when the issue affects model equations, estimators, identifying variation, sample inclusion/exclusion, treatment/control definitions, outcome construction, key covariates, fixed effects, clustering, weights, standard errors, units/scaling, merge keys, or timing/order where results could change.

Usually classify as `nonblocking-clarification` when the issue affects precision finer than the data contain, harmless label looseness, implementation details with no plausible impact on estimates, documented/inferable default behavior, or edge-case handling for cases absent from the observed data.

Anti-overconfidence rule: when unsure whether a mismatch is blocking or nonblocking, classify it as blocking unless Agent 0 can state why the distinction is unlikely to affect the model, sample, variables, or reported outputs.

Agent 0 finding IDs use one grep-friendly token:

```markdown
REFEREE2_FLAG[A0-YYYY-MM-DD-###]
Tier: blocking | nonblocking-clarification | documentation-nit
Scope: <path or scope component>
Issue fingerprint: <short stable description>
Evidence: <specific code/comment/provenance evidence>
Materiality rationale: <why this does or does not affect model/sample/variables/outputs>
Downstream assumption: <what Agent A should assume if nonblocking or overridden>
Blocks Agent A: yes | no
```

Agent 0 should include a separate `Possibly retired active overrides` section when an active ledger entry appears obsolete. It must not retire overrides automatically.

### Blocking Menu and Override Ledger

If Agent 0 finds uncovered blockers, parent presents this bounded menu and stops the audit until the user chooses:

```markdown
Agent 0 found blocking divergences. Referee2 cannot proceed to Agent A until each blocker is resolved or explicitly overridden.

For each blocker, choose one:
1. I will fix the code/comment outside referee2, then rerun.
2. Mark as intentional and add an active override.
3. Proceed with unresolved risk and add an active override.
4. Cancel the audit for now.
```

Option 1 stops referee2. Do not edit source inside the audit. The user fixes code/comments outside referee2 and reruns.

Options 2 and 3 append entries to `correspondence/referee2/referee2_overrides.md`. Override IDs use `REFEREE2_FLAG[OVR-YYYY-MM-DD-###]`; choose the next unused number for the date. Overrides are always user-decided and agent-entered: the parent may draft and append the ledger entry, but only after the user explicitly chooses an override for a specific Agent 0 blocker.

Ledger template:

```markdown
# Referee2 Override Ledger

If source code/comments are later changed so an override no longer applies, mark the entry `Status: retired` and explain the retirement reason. Agents read only active overrides for blocking decisions.

## REFEREE2_FLAG[OVR-YYYY-MM-DD-001]
Status: active
Tier: blocking-user-overridden | blocking-unresolved-user-proceed
Date created: YYYY-MM-DD
Date retired:
Created from finding: REFEREE2_FLAG[A0-YYYY-MM-DD-###]
Scope path: <path>
Issue fingerprint: <short stable description>
User decision: <verbatim or concise user decision>
Do not block if: <condition under which this override still applies>
Still block if: <condition under which this override no longer applies>
Spec flag required: yes
```

Agent 0 reads active overrides to avoid re-blocking adjudicated issues. Agent A reads active overrides only to encode localized `REFEREE2_FLAG[...]` assumptions in the spec. Agents B and C never read the override ledger.
