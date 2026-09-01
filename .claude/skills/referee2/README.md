# Referee 2: Systematic Audit & Replication Protocol

*A health inspector for empirical research.*

---

## Recommended Order: Blindspot First, Then Referee 2

Before running Referee 2, run `/blindspot` on your key figures and tables.

Blindspot catches perception problems — features of your output you haven't explained, problems hiding in plain sight (vices), and opportunities being overlooked (virtues). It runs during analysis, in your working session, at the moment output appears.

Referee 2 catches implementation problems — coding errors, replication failures, bad controls. It runs after the project is complete, in a fresh session.

**Running Blindspot first means that by the time Referee 2 audits the code, the interpretation has already been stress-tested.** A project that passes both is one where the code is correct *and* you understand what it's showing you.

```
Produce output → /blindspot → interpret and write → complete project → fresh terminal → /referee2
```

---

## What This Skill Does

Referee 2 is a five-audit protocol for catching errors, replication failures, and econometric problems in empirical work — before they become retractions, failed replications, or public embarrassments.

You invoke it after a project is complete, preferably in a **fresh terminal** with a Claude instance that has never seen the work. If invoked from a session that already touched the project, the skill must use its tainted-session catch: keep the parent session as orchestrator, spawn fresh role-specific subagents with only the verbatim invocation and confirmed paths, or cancel. That separation is what makes it independent. The Claude that built the pipeline cannot objectively audit it. Asking it to do so is like asking a student to grade their own exam.

**Invoke it with:** `/referee2 code path/to/project`

For code audits, the parent session may override default subagent model choices:

```text
/referee2 code path/to/project --Agent0=opus --AgentA=opus --AgentA-script=sonnet --BC=sonnet --parallel
```

By default, Agent 0 and a single lead Agent A use a frontier reasoning model; bounded per-script Agent A extraction workers and B/C replicators use a strong mid-tier model. Fanout subagents run sequentially by default to reduce usage-cap risk; add `--parallel` only when speed matters more than token-budget exposure. The parent session's own model is fixed before the skill is invoked and cannot be changed by the skill.

---

## The Five Audits

### Audit 1: Code Audit
Scrutinizes implementation for coding errors, missing value handling, merge diagnostics, and variable construction problems. Points to exact files and line numbers. Explains why each problem matters.

### Audit 2: Cross-Language Replication
Creates independent replication scripts in two additional languages (R → Stata + Python, or Stata → R + Python, etc.) and compares results to 6+ decimal places. The key insight: if Claude wrote R code with a subtle bug, asking the same Claude to write Stata will likely produce a *different* bug — cross-language comparison exploits that orthogonality to surface errors that single-language audit misses.

Replication is routed through a plain-language specification bottleneck. Agent 0 first classifies blockers, nonblocking clarifications, and documentation nits; only material blockers stop the audit. Downstream replication agents work from the spec and sealed expected outputs, not from the original code.

For large multi-script projects, the parent orchestrator may fan out bounded per-script Agent A extraction workers before a lead Agent A synthesizes the final spec. This is an orchestration choice made by the parent; subagents should not be expected to spawn their own subagents. If Agent A is fanned out, B/C should be fanned out on the same script or script-group units, sequentially unless the user supplied `--parallel`.

### Audit 3: Directory & Replication Package Audit
Checks folder structure, relative paths, naming conventions, master script, README, and dependencies. Scores replication readiness on a 1–10 scale. The standard: can a stranger reproduce this from scratch?

### Audit 4: Output Automation Audit
Verifies that tables and figures are programmatically generated — not manually typed or manually exported. Hardcoded in-text statistics are a major concern.

### Audit 5: Econometrics Audit
Verifies that the identification strategy is credible, specifications are correctly implemented, standard errors are clustered appropriately, parallel trends are tested (if DiD), and effect sizes are plausible.

---

## Critical Rule: Referee 2 Never Modifies Author Code

Referee 2 can read, run, and create its own audit artifacts. It cannot touch the author's files, even if the user asks for fixes during the audit. Only the author modifies the author's code. This separation ensures the audit is truly external.

---

## What Referee 2 Produces

1. **A referee report** (`correspondence/referee2/YYYY-MM-DD_round1_report.md`) — formal written audit with Major Concerns, Minor Concerns, and a verdict: Accept / Minor Revisions / Major Revisions / Reject.

2. **Audit and replication artifacts** (`code/replication/` and `correspondence/referee2/`) — scope manifests, specs, expected-output extracts, independent implementations in two additional languages, preserved first-run outputs, and comparison tables.

3. **A deck** (optional) — a compiled Beamer presentation summarizing the audit findings visually.

---

## The Revise & Resubmit Process

The workflow mirrors journal peer review:

1. **Author completes work** → opens fresh terminal → invokes `/referee2`
2. **Referee 2 audits** → files report with Major/Minor Concerns
3. **Author responds** — fixes or justifies each concern, documents changes
4. **Referee 2 re-audits** in a new fresh terminal, or via the tainted-session role-subagent catch
5. Repeat until verdict is Accept

---

## Referee 2 and Blindspot: Complements, Not Substitutes

**Both should be run. Neither replaces the other.**

| | Referee 2 | Blindspot |
|---|---|---|
| **Question** | Is this implemented correctly? | Can you see what's in front of you? |
| **Timing** | After the project is complete, fresh session | When output first appears, before writing |
| **Persona** | Health inspector with a checklist | Shklovsky — restoring perception |
| **Catches** | Coding errors, replication failures, bad controls | Overlooked problems (vices) and overlooked opportunities (virtues) |
| **Would have caught a merge error?** | Yes | Maybe |
| **Would have caught the t=1 spike?** | No | Yes |

**Why fresh sessions for Referee 2 but not Blindspot:**

Referee 2 requires fresh auditors because it's auditing implementation — the same Claude that built the code will rationalize its own choices. A fresh terminal is the cleanest route; the tainted-session catch can instead keep the parent as scheduler while spawning fresh role-specific subagents with restricted context. Independence is structural.

Blindspot runs in the same session because it's auditing perception — you need the person closest to the work, with a structured forcing function to look past what they expect to see.

**The workflow:**
1. Produce output → `/blindspot` → interpret and write
2. Complete project → fresh terminal → `/referee2`

---

## Installation

The skill lives at `.claude/skills/referee2/SKILL.md`. Shared persona and report conventions are in `referee2.md`; mode-specific protocols live in `deck.md` and `code.md` in the same folder.

To use it, ensure this repo is on your Claude Code skills path. Invoke with `/referee2 [mode] [path]` where mode is `deck` (for slide audits) or `code` (for empirical pipeline audits).

See the [skills README](../README.md) for general installation instructions.
