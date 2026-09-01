## Step -1: Tainted-session catch (run before anything else)

**Why this exists.** Referee2 only produces a credible audit if the auditing Claude has not previously touched the work being audited. `referee2.md` explains why: the Claude that built a pipeline cannot objectively review its own choices. If you, the assistant currently reading this skill, have prior context in this session that touched the project being audited, your audit is contaminated before it begins.

**Detection.** Before doing any code-audit work, inspect this session's context. Treat the session as **tainted** if any of the following is true:

- You have read, edited, or run files in the project being audited earlier in this session
- You have substantively discussed the project's content (its data, code, results, identification, etc.) earlier in this session

**Casual or unrelated prior turns do NOT count as taint.** Greetings, off-topic questions, and work on a different project are fine. The threshold is "did prior work touch *this* project?" When in doubt, treat as tainted.

**If the session is tainted, present the user with this two-choice catch:**

> ⚠️ Referee2 requires a fresh session to produce a credible audit — Claude cannot objectively review work it has previously touched (see "Why they are separated" in referee2 docs).
>
> This session has prior context that may compromise audit independence. Two options:
>
> **(a) Subagents** — I keep this parent session only as orchestrator, then spawn fresh role-specific subagents for Agent 0, Agent A, and Agents B/C. Convenient (no session restart), but any unstated context from our earlier conversation will not reach the subagents.
>
> **(b) Cancel** — You start a brand new session and re-invoke `/referee2`. Highest fidelity, since you provide the full invocation in a clean context.
>
> Which? (a / b)

There is no "(c) proceed anyway" option. Proceeding in a tainted main session produces an invalid audit; the menu is bounded by what produces a valid one. If the user reasons in conversation that the prior context was unrelated and asks to proceed anyway, exercise judgment per the detection threshold above (B) — the catch fired because of judgment, and judgment can clear it.

### If the user picks (a) Subagents — parent orchestration

When the user picks subagents, you (the parent) do not delegate the whole referee2 protocol to one subagent. Subagents cannot be assumed to spawn other subagents. The parent stays in charge of orchestration and spawns each role-specific fresh subagent itself:

1. Parent performs path enumeration/scope confirmation using only paths, not project narrative.
2. Parent writes or reuses the full scope manifest and reads active override ledger state.
3. Parent spawns Agent 0 and waits for the gate result.
4. If Agent 0 blocks, parent reports blockers to the user and stops.
5. If Agent 0 does not block, parent spawns Agent A and waits for `ready_for_BC=yes`. For large multi-script projects, the parent may instead fan out bounded per-script Agent A extraction workers, then spawn or retain a lead Agent A to synthesize their artifacts into the final spec and expected-output extracts. This fanout is parent-owned; per-script workers must not spawn subagents. The parent passes extraction artifact paths to the lead Agent A, not parent-written summaries of those artifacts.
6. Parent writes the restricted B/C manifest.
7. Parent spawns Agents B and C and waits for their triage results. By default, fanout subagents run sequentially to reduce usage-cap risk; if the user supplied `--parallel`, the parent may run same-stage fanout subagents in parallel. If the parent used Agent A fanout, B/C should be fanned out on the same script or script-group units: each Agent A extraction unit gets one B replicator and one C replicator in the assigned replication languages.
8. Parent aggregates role-subagent reports and writes the final report.

The discipline is still **transcription, not interpretation**. Quote verbatim. Do not paraphrase substantive project behavior in any role prompt.

#### Subagent model defaults and user overrides

The parent session's model is already fixed when the user invokes the skill; the skill cannot downgrade or upgrade the parent. It can choose model tiers only when spawning role subagents, subject to the host tool's available model names.

Default subagent model tiers:

| Role | Default model tier | Rationale |
|---|---|---|
| Agent 0 | frontier reasoning model, e.g. Opus or GPT-5.5 | Materiality judgments, econometric stakes, comment/code divergence, and scope ambiguity are high-risk. |
| Agent A, single lead translator | frontier reasoning model, e.g. Opus or GPT-5.5 | Full-pipeline compression into a prose/math spec is high-risk when one agent handles the whole scope. |
| Per-script Agent A extraction workers | strong mid-tier model, e.g. Sonnet or GPT-5.4 | Bounded script transcription is mostly extraction; the lead Agent A owns synthesis. |
| Agents B/C | strong mid-tier model, e.g. Sonnet, GPT-5.4, or GPT-5.3-Codex | Replication work needs coding reliability more than frontier judgment. |

Respect explicit user model choices. The user may add optional flags to the `/referee2` invocation:

```text
--Agent0=<model>
--AgentA=<model>
--AgentA-script=<model>
--BC=<model>
--parallel
```

`--BC=<model>` applies to both B and C. B and C exist only to run different replication languages, so they use the same model selection. Exact model names are host-dependent; accept common aliases when unambiguous, such as `opus`, `sonnet`, `gpt5.5`, `gpt-5.5`, `gpt5.4`, `gpt-5.4`, `gpt5.3-codex`, `gpt-5.3-codex`, `gpt5.4-mini`, and `gpt-5.4-mini`.

By default, parent-owned fanout runs sequentially: complete one per-script Agent A worker before starting the next, and complete each B/C replication unit before starting the next unit. This avoids spending large amounts of tokens on multiple one-shot subagents that may all fail if the user hits a usage cap mid-stage. If the user supplies `--parallel`, the parent may run same-stage fanout workers concurrently when the host supports it. `--parallel` does not change the isolation rule: each subagent still gets only its assigned role context and must not spawn further subagents.

If the requested model is unavailable, tell the user which role cannot use it and fall back to the nearest available model in the same tier. Do not silently ignore user model choices.

Role-subagent prompt header template:

```
You are running one role in the referee2 protocol in a fresh subagent context.
The parent session is orchestrating the protocol. You must not spawn further
subagents.

The user invoked this skill via:

  User invocation (verbatim):
  > /referee2 <args>

  User's invocation message (verbatim, if anything beyond the bare command):
  > <full message text>

Mode: <deck|code>
Target: <absolute path to file or directory>
Role: <Agent 0|Agent A|Agent B|Agent C>

Read ~/.claude/skills/referee2/code.md and execute the protocol from
the instructions for your assigned role only. Do not assume any prior context.
The user's verbatim text above plus the manifest/spec paths supplied by the
parent are your only specification.
```

#### Path enumeration (when the user's invocation is vague)

If the user's invocation is not a precise path (e.g., "audit everything we worked on this session," "the new code," empty target), do NOT skip enumeration and let the role subagents flounder. Enumerate concrete paths from this session's tool history, then **confirm with the user before spawning Agent 0:**

> I'll audit these files with fresh referee2 subagents (enumerated from this session's tool use):
>
> ```
> /path/to/a.do
> /path/to/b.R
> /path/to/c.py
> ```
>
> Add, remove, or proceed?

After user confirms, include the confirmed list in the full scope manifest or Agent 0 prompt under a `Session-enumerated audit scope` heading.

**Hard rule for enumeration: paths only, no narrative.** Do NOT include "this script does X," "we use Y approach," or any editorialization. Path strings are objective transcription; everything else is interpretation that contaminates the subagent's independence. If the user's invocation IS a precise path already, skip enumeration entirely — they've specified scope.

### If the user picks (b) Cancel

Tell the user: "Understood — start a new terminal session and re-invoke `/referee2 <args>` there for the cleanest audit." Do not proceed.

### Iterative re-invocation in the same parent session

After a role-subagent run completes and the user addresses findings (updates code, fills spec gaps), the user may re-invoke referee2 in the same parent session for a second audit. This is fine — each role subagent is fresh by virtue of being a subagent, regardless of how many prior subagents the parent has spawned. The independence requirement is about the *auditor*, not the user-Claude collaboration.

**However:** when constructing the prompt for a follow-up role subagent, **NEVER include prior-audit findings in the prompt** unless the role is explicitly resuming from a prior artifact path. Each subagent audits the current state on its own terms — pass current code + current spec + scope, never prior-audit narrative. Two reasons:

- **Anchoring:** the new subagent would look for the same problems and possibly miss new ones
- **Confirmation:** the new subagent might rationalize that previous findings were "addressed" without independently verifying

Same discipline as path enumeration: transcribe the current state, never the audit history.

---

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

### Required Subagent Prompt Components

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

**Spec template — prose for substance, math notation for the model. Not pseudo-code.**

Pseudo-code is one paraphrase away from the original code: it primes the auditor to write the same structural pattern in the target language, defeating orthogonality. Prose forces commitment to *what* without prescribing *how*. Math notation pins down the model unambiguously without prescribing implementation.

The spec must declare input data paths, not source-of-truth output paths. Output artifact paths belong in sealed comparison instructions, not in the substantive spec.

The spec must contain these seven sections plus an input-data declaration. If any flags affect replication, include a sanitized `REFEREE2_FLAG assumptions for replication` section immediately after `Input data`.

```markdown
# Specification: <project / scope>

## Input data
Primary analysis dataset:
- Path: data/derived/panel_daily.dta
- Unit of observation: county-day
- Required variables: fips, date, mortality_rate, heat_index, controls...

## REFEREE2_FLAG assumptions for replication
- REFEREE2_FLAG[A0-YYYY-MM-DD-###]
  Downstream assumption: <implementation-relevant assumption only>
- REFEREE2_FLAG[OVR-YYYY-MM-DD-###]
  Downstream assumption: <implementation-relevant assumption only>
- REFEREE2_FLAG[FIG-YYYY-MM-DD-###]
  Downstream assumption: <figure replication/human-comparison assumption only>

## 1. Model
Equation in math notation; specify regressors, fixed effects, standard error
type (HC1, HC2, HC3, cluster-robust, bootstrap), and clustering level.

Example:
$$\log w_{it} = \beta s_i + \gamma a_{it} + \delta a_{it}^2 + \mathbf{X}_{it}'\boldsymbol{\eta} + \alpha_{st} + \varepsilon_{it}$$
SE: cluster-robust, clustered at individual ($i$).

## 2. Sample construction
Eligibility criteria (ages, geography, time period), explicit exclusions.
Prose, not code. State the universe and what is dropped from it.

## 3. Data dictionary and units
| Variable | Role | Unit / scale | Observed range or support | Notes |
|---|---|---|---|---|
| treatment_prob | Treatment | Probability, 0-1 scale | 0 to 0.82 | Not percentage points |

## 4. Variable construction
Transformations, recoding, derived variables, units. Order matters when later
constructions depend on earlier ones — state the order in prose.

## 5. Missingness and edge-case handling
**This section is mandatory and must not be skipped.**
- Missingness: listwise deletion / pairwise / imputation (specify method)
- Zeros and negatives in logs: how handled
- Tied values: how broken
- Panel gaps: how treated (drop, fill, ignore)
- Anything else where a sensible default could go either way

If the original code is silent on a question here, write "ORIGINAL CODE
SILENT" and pick a defensible default. Document the choice. The replication
implements your documented choice.

## 6. Target parameter
The estimand and its interpretation in plain English. What does the headline
number actually represent?

## 7. Identification
The conditional-independence assumption being made. State as an equation
where appropriate, e.g.:
$$E[\varepsilon_{it} \mid s_i, \mathbf{X}_{it}, \alpha_{st}] = 0$$
```

The `REFEREE2_FLAG assumptions for replication` section is not an audit trail. Include only:

- `nonblocking-clarification` flags that affect implementation assumptions
- active override flags when `Spec flag required: yes`
- `figure-human-comparison` flags that tell B/C how to handle non-numeric figure comparisons

Do not include documentation nits, Agent 0 evidence, Agent 0 materiality rationale, user decision text, override ledger text, full scope/provenance narrative, or prior report context. Those belong in Agent 0 output, expected-output notes, override ledger, or final report.

**The orthogonality test for the spec:** could two competent econometricians, given this spec, produce *structurally different but mathematically equivalent* implementations? If yes → the spec is doing its job. If both would write identical-shaped code → the spec has collapsed back into the original.

### Comment handling — comments are claims to verify, not guides to trust

Well-documented code is a net asset for auditing — comments are the self-report against which the auditor verifies behavior. But comments create a specific bias risk in two places:

1. **Comment-anchored reading** can hide off-by-ones, sign errors, and unit mismatches. A comment saying "loop over i = 1..n" before code that says `for i in range(n)` (which is 0..n-1) gets skimmed past.
2. **Comments-and-code-together translation** in cross-language replication imports the conceptual model into the target language, defeating orthogonality (this is what the spec bottleneck above protects against).

**Rule for the Code Audit:** read the code first, treating comments as `<!-- -->` (visible but parsed last). Verify behavior independently. Then check whether the comments accurately describe what the code does. **Any comment/code divergence is a finding, not an annotation to silently reconcile.** Classify each finding using the Agent 0 materiality tiers. Examples that must be flagged:

- Comment says "robust SE clustered at firm" but code uses HC1
- Comment says "drop observations with missing wages" but code drops missing in any regressor
- Comment says "log transform" but code uses log1p (or vice versa)
- Comment specifies one functional form, code implements another

This audit is operationalized as Agent 0 in the four-agent architecture above. Agent 0 returns findings to the parent. Only material `blocking` findings stop Agent A. Nonblocking clarifications proceed as localized `REFEREE2_FLAG[...]` assumptions; documentation nits are reported but do not enter the spec unless they affect interpretation.

Agent A always writes the spec from executable code behavior. If the user says comments are correct and code is wrong, stop the audit so author code can be fixed outside referee2.

### Expected Outputs and Sealed Targets

Existing output artifacts are the source of truth by default. Expected-output files should usually be structured extractions from the project's existing tables, figures, or result files, not newly generated outputs. Agent A must not rerun original code to refresh, regenerate, or validate source outputs before extraction. Rerunning original code is allowed only when the user explicitly requested an Output Automation Audit rerun/reproducibility check, and that check is parent-owned diagnostic evidence rather than Agent A work.

Agent A writes:

- `code/replication/YYYY-MM-DD_roundN_expected_outputs_<scope>.csv` for table-like numeric targets by default
- `code/replication/YYYY-MM-DD_roundN_expected_outputs_<scope>.json` when outputs are nested, scalar dictionaries, or multi-panel objects where CSV would obscure structure
- `code/replication/YYYY-MM-DD_roundN_expected_outputs_<scope>_notes.md` always

For table-like outputs, use these columns where applicable:

```csv
output_id,model,term,statistic,value,unit,source_artifact,source_location,notes
```

The notes file documents:

- source artifact(s)
- provenance: existing artifact treated as source of truth; rerun not requested / user-requested rerun attempted and matched / user-requested rerun attempted and differed
- extraction choices
- stale-output concerns, if any
- sealed-output instructions for B/C

Stale-output checks are separate from expected-output extraction. Agent A should not block B/C merely because output artifacts may be stale and should not regenerate outputs to resolve staleness. Block B/C only if no meaningful source-of-truth expected values can be extracted or defined for the target output. If artifacts appear stale, record the concern in the expected-output notes and final report.

### Optional Output Automation Rerun

Run the author's original entrypoint for bytewise or numeric output-regeneration checks only when the user explicitly asks for that check in the referee2 invocation or follow-up. Do not infer this from ordinary code-audit mode.

When requested, the parent owns the rerun check after Agent A has extracted expected outputs from existing artifacts. The parent may run the original entrypoint and compare pre-existing source artifacts against regenerated artifacts or post-run hashes. Record the result in the final report and expected-output notes as parent-owned Output Automation Audit evidence. A rerun mismatch is an audit finding; it does not authorize Agent A, B, C, or the parent to edit author code.

Parent writes a physical restricted manifest for B/C at `correspondence/referee2/YYYY-MM-DD_roundN_restricted_manifest.md`. It contains:

```markdown
## You may read before first run
- code/replication/YYYY-MM-DD_roundN_spec_<scope>.md
- code/config.do only for path assignment; do not inspect analysis logic
- data/derived/panel_daily.dta only to confirm schema/units and run replication

## Sealed until first-run outputs are saved
- code/replication/YYYY-MM-DD_roundN_expected_outputs_<scope>.csv
- code/replication/YYYY-MM-DD_roundN_expected_outputs_<scope>_notes.md
- output/tables/main_results.tex

## You must not read
- original entrypoint scripts
- sourced analysis/helper scripts
- existing output artifacts before first-run outputs are saved
- expected-output files before first-run outputs are saved
- prior referee2 reports
- override ledger
- full scope manifest
```

B/C may receive sealed target paths up front, but must not open them until after writing the replication script, running it to completion, and saving first-run outputs. Each B/C report must state:

```markdown
Expected outputs opened after first-run outputs saved: yes/no
First-run output path: <path>
```

B/C must also write a round-specific first-run lock file after first-run outputs are created and before opening expected outputs or source outputs:

```markdown
correspondence/referee2/YYYY-MM-DD_roundN_<language>_first_run_lock.md
```

Lock file contents:

```markdown
# Referee2 First-Run Lock

Language: <R|Python|Stata>
Round: YYYY-MM-DD_roundN
Spec path: <path>
First-run script path: <path>
First-run output path: <path>
Timestamp first-run output saved: <timestamp>
Expected outputs opened before first-run: no
Source outputs opened before first-run: no
```

B/C may revise after opening expected outputs, but must preserve first-run scripts and outputs. Use artifact names like:

```markdown
code/replication/referee2_replicate_R_first_run.R
code/replication/referee2_R_first_run_outputs.csv
correspondence/referee2/YYYY-MM-DD_roundN_R_first_run_lock.md
code/replication/referee2_replicate_R_revised.R
code/replication/referee2_R_revised_outputs.csv
code/replication/referee2_R_revision_log.md
```

If a replication attempt fails before creating first-run outputs, do not write the first-run lock. Preserve the failed script and a failure log, then make diagnostic changes only to referee-owned replication artifacts or environment-access helpers while expected/source outputs remain sealed. The first successful run that creates outputs becomes the first-run artifact and receives the lock. Revision logs classify each change as `spec misread`, `package default mismatch`, `spec gap`, `original-code discrepancy`, or `numerical/formatting issue`.

Formatting differences are immaterial unless they change substantive results. Do not revise solely to match table layout, labels, stars, decimal display, column order, LaTeX formatting, or file naming.

For figures, Agent A should identify numeric targets where possible: plotted points, event-study estimates and confidence intervals, coefficient plot values, bin means, histogram/bin counts, or sample sizes behind plotted groups. If a numeric backing file exists, use it as expected output. If no stable numeric target exists, create a flag:

```markdown
REFEREE2_FLAG[FIG-YYYY-MM-DD-001]
Tier: figure-human-comparison
Scope: output/figures/<figure>.pdf
Issue fingerprint: figure output is not reducible to stable numeric targets; human visual comparison required.
Downstream assumption: B/C should reproduce the figure from the plain-language spec and save rendered outputs; referee2 will not classify visual match automatically.
```

First-run figures use `code/replication/referee2_<language>_first_run_<figure_slug>.<ext>`. Revised figures use `code/replication/referee2_<language>_revised_<figure_slug>.<ext>`. Numeric backing outputs use the same stem with `_data.csv` or `_data.json`. B/C may make qualitative comparisons only after first-run artifacts are saved, and must label those comparisons qualitative unless numeric targets exist.

### Discrepancy triage — classify at finding-time

When the cross-language replication produces different numbers, classify each discrepancy IMMEDIATELY into one of three categories before drilling further. The category determines what to do next.

| Category | What it means | What to do |
|---|---|---|
| **Substantive** | Different model, estimator, identifying variation, or target parameter | Real finding. Deep dive. Likely a bug in original or replication. |
| **Ancillary, specified in spec** | The replicator implemented section 2/3/4 contrary to the spec | Auditor error. Fix the replication and rerun. |
| **Ancillary, absent from spec** | Replication used a different default for something the spec didn't pin down | **Sensitivity finding, not a bug.** Report as: "result depends on choice X; you may want to make that intentional." |

The third category is the key reframe. It is NOT "wasted time hunting a phantom bug." It is a finding: *the headline number is sensitive to a choice the author didn't realize they were making.* Published replication failures often trace back to undocumented nuisance choices, not to bugs in either implementation.

**Output format reflects the triage** — discrepancies are tagged with category and treated differently:

```
Cross-language comparison (Stata original vs. R replication):

Coefficient on schooling:
  Stata: 0.087 (SE 0.012)
  R:     0.091 (SE 0.013)
  Diff:  +0.004 (4.6%)
  Category: Ancillary, absent from spec
  Reason: Stata default = listwise deletion; R replication = complete-case on
          regressors only. Spec section 4 did not pin this down.
  Recommendation: pin down missingness in spec section 4 and rerun both.

Coefficient on age²:
  Stata:  -0.0003
  R:      -0.0003
  Diff:   <0.001%
  Category: Match (within numerical precision)
```

For each discrepancy, the workflow is:
1. **Classify** into one of the three categories
2. **Conjecture** the specific source (package default, syntax, precision, spec gap)
3. **Test** the conjecture where feasible (e.g., force matching missingness handling and re-run)
4. **Report** the finding with category tag and evidence

### The Five Audits

Perform the five audits from `~/.claude/skills/referee2/referee2.md`:
1. Code Audit
2. Cross-Language Replication
3. Directory & Replication Package Audit
4. Output Automation Audit
5. Econometrics Audit

Use the **scope calibration table** from the persona to determine intensity.

### Critical Rule: NEVER Modify Author Code

You READ, RUN, and CREATE your own audit artifacts. You NEVER edit the author's code. Audit independence requires separation.

### Output
1. Spec file at `code/replication/YYYY-MM-DD_roundN_spec_<scope>.md` (written by Agent A)
2. Expected-output extraction file at `code/replication/YYYY-MM-DD_roundN_expected_outputs_<scope>.<csv|json>` plus `YYYY-MM-DD_roundN_expected_outputs_<scope>_notes.md` (written by Agent A)
3. Full scope manifest and restricted B/C manifest in `correspondence/referee2/`
4. Agent 0 findings at `correspondence/referee2/YYYY-MM-DD_roundN_agent0_findings.md`
5. First-run lock files at `correspondence/referee2/YYYY-MM-DD_roundN_<language>_first_run_lock.md`
6. Replication scripts in `code/replication/referee2_replicate_*.{R,do,py}` (written by Agents B and C)
7. Preserved first-run outputs, optional revised outputs, and revision logs
8. Comparison tables showing each replication's outputs vs. expected outputs
9. Discrepancy diagnoses with source classification (per the triage table)
10. Formal referee report in `correspondence/referee2/`

---

## Subagent operationalization (when running under the tainted-session catch)

When referee2 runs under Step -1's tainted-session catch, the parent session remains the orchestrator. Do not spawn one "referee2 subagent" and expect it to run the whole protocol; role subagents may not be able to spawn other subagents. The parent must spawn each fresh role subagent directly and wait for that role's return before deciding the next step.

For large multi-script code audits, the parent may choose a fanout Agent A pattern: spawn one bounded extraction worker per script or coherent script group, then have a lead Agent A synthesize the final seven-section spec and expected-output artifacts from those extraction artifacts. Use this only when it reduces context bloat or cost without weakening the spec bottleneck. Per-script workers write extraction notes only; they do not write the final spec, run replications, compare outputs, or spawn further subagents. The parent passes extraction artifact paths to lead Agent A rather than summarizing the workers' findings. If Agent A is fanned out, B/C should be fanned out on the same script or script-group units. Run fanout units sequentially by default; use parallel fanout only when the user supplied `--parallel`.

The Agent 0 gate is materiality-based:

- No blockers: parent spawns Agent A next.
- Active overrides: parent proceeds to Agent A, and Agent A carries override flags into the spec.
- Nonblocking flags: parent proceeds to Agent A, and Agent A carries relevant flags into the spec.
- Blocking findings not covered by active overrides: parent stops with `Status: blocked-on-user-review` and reports Agent 0's findings plus the blocking menu.
- Agent A handoff unavailable after Agent 0: parent stops with `Status: partial-audit-replication-blocked` after preserving Agent 0 findings. A later invocation may resume at Agent A if source state is unchanged.
- B/C handoff unavailable after Agent A: parent stops with `Status: partial-audit-replication-blocked` after preserving Agent A artifacts. A later invocation may resume at B/C if source state is unchanged.

If the parent stops on blockers, the user can fix code/comments outside referee2, add overrides, cancel, or rerun after changes. A later fresh Agent 0 subagent re-runs against the current source; it never relies on prior audit narrative.

If the parent stops because a role handoff is unavailable, return only the resumable artifact paths for completed stages. On a later invocation, the parent may offer to resume from the next missing role if those artifacts are the newest matching round for the same scope and the source files/source-output artifacts listed in the full scope manifest have not changed. If source state changed, start over at Agent 0.

### Liberal gap-flagging in Agent A

Even after Agent 0's audit is clean, Agent A may find the original code is silent on something in spec section 5 (missingness, edge cases) or sections 2/4 (sample, variable construction). Agent A cannot pause to ask the user — it is also single-shot. Do NOT skip the section and do NOT refuse to proceed. Do both:

1. **Record the gap explicitly** in the spec:
   ```
   ## 5. Missingness and edge-case handling
   ORIGINAL CODE SILENT on missingness — no explicit drop_na, no `if !missing()`, no `dropna()`.
   ```
2. **Pick a defensible default and document the choice:**
   ```
   Replication assumption: listwise deletion across all model variables
   (matches Stata's `regress` default; this is the most common econometric
   convention). If author intended otherwise, this becomes an "Open question
   for the user" in the final report.
   ```

Agent A proceeds with documented assumptions. Refusing to proceed because of gaps would make the audit unactionable.

**The triage table is the report format, not mid-run dialogue.** Classify each discrepancy yourself, include reasoning, present the three categories distinctly in the final report.

**Final report structure (subagent return value after a completed B/C handoff):**

```markdown
## Spec
[Path to the seven-section spec; do not paste the full spec unless the user asked for inline detail]

## Substantive discrepancies (likely real findings)
[List with deep-dive diagnosis]

## Ancillary spec violations (replication errors)
[List — fix-and-rerun within this run if time permits, else flag]

## Sensitivity findings (results depend on assumptions absent from original code)
[List with: which spec section, what default I assumed, what alternative would do]

## Open questions for the user (cannot be resolved without input)
[List of spec gaps where my default may be wrong; user can resolve in a follow-up invocation]

## Other audit findings
[Code audit, directory audit, output automation audit, econometrics audit findings]
```

**Resolution loop.** After the parent aggregates role-subagent results, the parent surfaces the report to the user. If the user wants to resolve open questions, they update the code and/or provide spec answers, then re-invoke referee2 in the same parent session. New fresh role subagents run against the updated state. Per Step -1's "Iterative re-invocation" rule: new role-subagent prompts must NOT include the prior audit's findings — only the current code, current spec, and scope.

**Resume loop.** If a prior round stopped with `partial-audit-replication-blocked`, a later invocation may resume from the next missing role rather than rerun completed stages. If Agent 0 completed but Agent A did not, resume at Agent A. If Agent A completed but B/C did not, resume at B/C. The parent must ask the user before resuming and must verify unchanged source state using file paths and timestamps or hashes from the prior scope/spec artifacts. Resume prompts receive only the artifacts needed for the next role; they do not receive prior report narrative or the reason the handoff failed.

---

## Filing the Report

### Report Format
Use the formal referee report template from `~/.claude/skills/referee2/referee2.md`:
- Summary
- Status: `passed`, `blocked-on-user-review`, `partial-audit-replication-blocked`, `proceeding-with-nonblocking-flags`, `human-figure-comparison-required`, or `failed-substantive-discrepancy`
- Status is the audit workflow state, not the substantive referee verdict.
- Findings by audit
- Major Concerns (must be addressed)
- Minor Concerns (should be addressed)
- Questions for Authors
- Verdict
- Verdict is the substantive referee judgment: Accept, Minor Revisions, Major Revisions, or Reject. If status is `blocked-on-user-review`, write `Verdict: Not reached`.
- Prioritized Recommendations

### File Locations
- Full scope manifest: `correspondence/referee2/YYYY-MM-DD_roundN_scope.md`
- Restricted B/C manifest: `correspondence/referee2/YYYY-MM-DD_roundN_restricted_manifest.md`
- Agent 0 findings: `correspondence/referee2/YYYY-MM-DD_roundN_agent0_findings.md`
- First-run lock files: `correspondence/referee2/YYYY-MM-DD_roundN_<language>_first_run_lock.md`
- Override ledger: `correspondence/referee2/referee2_overrides.md`
- Report: `correspondence/referee2/YYYY-MM-DD_roundN_report.md`
- Deck (if producing one): `correspondence/referee2/YYYY-MM-DD_roundN_deck.tex`
- Replication scripts: `code/replication/referee2_replicate_*.{R,do,py}`

If these directories don't exist, create them.

---

## Remember

The replication scripts you create are permanent artifacts. They prove the results were independently verified — or they prove they weren't. Either outcome is valuable. Do the work.
