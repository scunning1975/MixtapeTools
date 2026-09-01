---
name: tikz
description: Audit and fix residual TikZ visual collisions in any .tex file. A downstream repair tool — not a safety net. The upstream defense is /beautiful_deck Step 4.4, which writes safe TikZ from the start. Use /tikz when labels overlap arrows, text sits on boxes, or arrows cross each other. Applies mathematical gap calculations and Bézier depth formulas — no eyeballing.
allowed-tools: Bash(pdflatex*), Bash(grep*), Bash(ls*), Bash(~/.claude/skills/tikz/scripts/audit_passes.sh:*), Read, Edit, Glob
argument-hint: [path/to/file.tex]
---

# TikZ Collision Audit

**Purpose**: Find and fix residual visual collisions in TikZ figures in a given `.tex` file. Labels on arrows, text inside boxes, arrows crossing arrows — this skill catches them using measurement, not intuition.

**The fundamental rule**: Claude cannot reliably eyeball where TikZ elements land. All placement must be verified mathematically before declaring it safe.

---

## Critical context: this is a repair tool, not the primary defense

`/tikz` runs **after** TikZ has been generated. It audits existing code and fixes what it finds. But it cannot reliably fix diagrams that were never built with measurement in mind.

**The upstream defense is `/beautiful_deck` Step 4.4**, which writes safe TikZ from the start: explicit node dimensions, directional keywords on every edge label, coordinate map comments, canonical templates, no `scale` on complex diagrams.

**When Step 4.4 was applied**: `/tikz` should find few or no issues. Run it as a check.

**When Step 4.4 was NOT applied** (legacy TikZ, hand-written diagrams, inherited decks): `/tikz` does its best, but expect more findings, more iteration, and lower reliability on autosized nodes and scaled diagrams.

---

## Step 1: Read the rule book

The full rule book — every formula, every clearance table, every worked example — lives at `~/.claude/skills/tikz/tikz_rules.md`. **Read it first.** This SKILL.md is the operational checklist; `tikz_rules.md` is the reference. Do not try to execute the audit from memory.

The same rule book is read by `/beautiful_deck` Step 4.4 (generation-time prevention). Single source of truth.

---

## Step 2: Identify the file and run the pre-check

If the user specified a file, use it. If not, ask. Then:

```bash
~/.claude/skills/tikz/scripts/audit_passes.sh [file].tex
```

Get a sense of scope: how many TikZ diagrams, how many frames, how many arrows.

### Pre-check: were the generation rules followed?

Quickly assess whether the TikZ was written safely using the autosized-node, scale, and coordinate-map sections from `audit_passes.sh`.

- **Autosized nodes widespread** → repair reliability is lower. Upstream fix: add explicit dimensions. Consider doing that first.
- **`scale` on complex diagram** → coordinates compress but text does not. Compensation in Passes 2–5 is fragile. Upstream fix: redesign at intended size.
- **No coordinate map** → audit takes longer; spatial relationships must be reverse-engineered from code.

---

## Step 3: Run the six passes from `tikz_rules.md`

For each `tikzpicture` in the file, run all six passes **in order**. Follow the protocols and formulas in `tikz_rules.md` exactly — do not paraphrase or estimate.

| Pass | Target | Rule-book section |
|---|---|---|
| **0** | Cross-slide consistency | `tikz_rules.md` § Pass 0 |
| **1** | Bézier curves — do this FIRST | `tikz_rules.md` § Pass 1 |
| **2** | Edge-label gap calculations | `tikz_rules.md` § Pass 2 |
| **3** | Arrow-label positioning keywords | `tikz_rules.md` § Pass 3 |
| **4** | Boundary Rule (labels vs drawn shapes) | `tikz_rules.md` § Pass 4 |
| **5** | Margin spacing | `tikz_rules.md` § Pass 5 |

Use the candidate sections from `audit_passes.sh` as the starting index for Passes 0, 1, and 3.

---

## Step 4: Pass 6 — Debug bounding-box verification (skill-specific, on demand)

When Passes 1–5 flagged collisions but the source-level fix isn't obvious from coordinate math, read `~/.claude/skills/tikz/debug_bounding_box.md` and apply the red-outline pass to force the bounding boxes into view. Last-resort localization tool; do not run by default.

---

## Step 5: Fix, recompile, repeat

After making fixes:

```bash
~/.claude/skills/tikz/scripts/audit_passes.sh [file].tex --compile
```

Must return zero lines. Fix any new warnings introduced by repositioning. Repeat until clean.

---

## Step 6: Re-audit the ENTIRE file after any fix

One collision fix often reveals a second one nearby, or introduces a new label that crowds a different object. After every change, re-run Passes 1–5 on **all** TikZ figures in the file — not just the one you just touched.

Use the TikZ picture count from `audit_passes.sh` to confirm how many diagrams need a clean bill of health.

---

## Known limitations

See `~/.claude/skills/tikz/tikz_rules.md` § Known Limitations. The summary: autosized nodes, `scale` on complex diagrams, math-mode label widths, nested `tikzpicture` environments, and `\foreach` loops are the cases where `/tikz` is least reliable. The better fix is almost always upstream (rewrite the TikZ safely per `tikz_rules.md`) rather than downstream repair.
