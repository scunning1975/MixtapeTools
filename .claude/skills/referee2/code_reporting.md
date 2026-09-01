## Discrepancy Triage and Reporting

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
