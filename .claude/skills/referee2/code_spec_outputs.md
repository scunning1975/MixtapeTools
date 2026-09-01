## Specification and Sealed Outputs

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
