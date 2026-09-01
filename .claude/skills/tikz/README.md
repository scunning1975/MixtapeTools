# TikZ Collision Audit (`/tikz`)

> **A repair tool for residual TikZ collisions — not a safety net for bad generation.**

`/tikz` catches what `pdflatex` doesn't: labels sitting on arrows, text bleeding into box edges, Bézier curves passing through other labels, arrows pointing to the wrong node. LaTeX reports none of these. Humans usually miss them on first review. `/tikz` finds them by computing the actual geometry.

## The critical distinction: prevention vs. repair

**`/tikz` is a repair tool.** It runs measurement-based checks on existing TikZ code and fixes what it finds. But it cannot reliably fix diagrams that were never built with measurement in mind — autosized nodes, missing directional keywords, `scale` factors that compress coordinates but not text. These upstream generation problems produce collisions that are structurally unfixable by any audit pass.

**The upstream defense is `/beautiful_deck` Step 4.4**, which writes safe TikZ from the start: explicit node dimensions, coordinate maps, directional keywords on every edge label, canonical templates for common diagram types, and a strict prohibition on `scale` for complex diagrams. When Step 4.4 does its job, `/tikz` has little to find. When Step 4.4 is skipped — or when you're auditing TikZ that was written outside of `/beautiful_deck` — `/tikz` does its best, but the success rate depends entirely on how the TikZ was generated.

**The pipeline**: prevention (Step 4.4) → compile → residual repair (`/tikz`).

## The fundamental rule

**Claude cannot reliably eyeball where TikZ elements land.** Anywhere a label's position depends on arithmetic — gap widths, curve depths, scale factors, node boundaries — the placement must be verified mathematically before it is declared safe. Estimating "looks about right" is the failure mode. `/tikz` replaces estimation with formulas.

## What it catches

| Problem | Why LaTeX misses it | How `/tikz` catches it |
|---|---|---|
| Label overlaps a Bézier curve | Curve geometry is runtime-computed | Computes `max_depth = (chord/2) × tan(bend/2)` and checks labels against the safe zone |
| Edge label between two nodes is wider than the gap | LaTeX places it anyway; the text just runs under the next node | Compares estimated text width to the usable gap (`center-to-center − half-width(A) − half-width(B) − 0.6cm padding`) |
| `node[...]{text}` on an arrow without `above`/`below`/`left`/`right` | Valid syntax | Greps for missing directional keywords |
| Text inside or touching a drawn shape | Compiles silently | Applies the Boundary Rule: 0.4cm minimum clearance from every circle, rectangle, or filled shape |
| Two Bézier curves crossing each other | No warning | Checks bend direction compatibility across nearby arrows |
| `scale=0.8` shrinks coordinates but not text | Geometrically valid | Recalculates all gaps accounting for the scale factor |
| Label clipped by slide margin | Within the page box | Margin check: every object ≥ 0.5cm from the slide edge |
| Same diagram on multiple slides has inconsistent positions | Each instance compiles independently | Pass 0 cross-slide consistency check |

## The six passes

`/tikz` runs a fixed, ordered protocol. Each pass targets a specific class of collision. Full formulas, clearance tables, and worked examples live in [`tikz_rules.md`](tikz_rules.md) (in this folder).

| Pass | What it checks |
|---|---|
| **Pass 0** | Cross-slide consistency — when the same diagram appears on multiple frames, colors, positions, and font sizes must be identical except for the deliberate change. |
| **Pass 1** | Bézier curves first. Computes max curve depth from chord length and bend angle, adds 0.5cm safety margin, checks every label in the danger zone. Also checks for curves crossing other arrows. |
| **Pass 2** | Edge label gap calculations. For every label between two nodes, estimates label width (character count × font size), compares to the usable gap, flags where width exceeds gap. |
| **Pass 3** | Arrow-label positioning keywords. Every `node[...]{}` on an arrow must carry `above`, `below`, `left`, `right`, `anchor=`, `pos=`, or `midway`. |
| **Pass 4** | Boundary Rule. For every drawn shape, computes the boundary and flags any label within 0.4cm. Same rule applies to matplotlib / ggplot2 patches. |
| **Pass 5** | Margin check. Minimum clearances enforced across labels, axes, arrows, and slide edges. |
| **Pass 6** | **Debug bounding-box verification (skill-specific).** Add red outlines to every node, recompile, inspect for overlapping rectangles. The only reliable way to spot residual visual collisions Claude cannot eyeball. |

## The re-audit rule

**One collision fix almost always reveals another one.** After any change, `/tikz` re-runs Passes 0–5 on *all* TikZ figures in the file, not just the one that was touched. Moving a label to fix one collision can push it into another node, or reveal a previously hidden overlap. The skill treats the audit as complete only when a full pass on the entire file returns zero violations *and* a subsequent `pdflatex` shows zero Overfull, Underfull, or font warnings.

## Usage

```
/tikz path/to/deck.tex
```

`/tikz` will identify every `tikzpicture` environment in the file, run the six passes on each, and produce a report with exact line numbers for every violation. It applies fixes directly to the source file, then recompiles to verify.

## When to use it

- **Always after `/beautiful_deck`** — the skill invokes `/tikz` automatically as part of the visual cleanup step. Because Step 4.4 now writes safe TikZ from the start, `/tikz` should find few or no issues in new decks. Re-run manually after any significant edit to a diagram.
- **After any TikZ edit** — adding a new node, changing a bend angle, repositioning a label. Don't trust visual inspection alone; run the math.
- **Before shipping a deck** — final pre-flight check.
- **When a diagram "looks wrong" but you can't say why** — `/tikz` will find the exact measurement causing the discomfort.
- **On TikZ written outside of `/beautiful_deck`** — legacy diagrams, inherited decks, hand-written TikZ. Expect more findings and more iteration.

## Known limitations

- **Cannot fix autosized nodes reliably.** If a `\node` has no explicit `minimum width`/`minimum height`, its rendered dimensions depend on text content and font — information `/tikz` can only estimate. The fix is upstream: write explicit dimensions.
- **`scale` factor creates invisible collisions.** `scale=0.55` shrinks coordinates but not text. Compensation is fragile. The fix is upstream: never use `scale` on complex diagrams.
- **Math-mode label widths.** `$\hat{\beta}_{it}$` is wider than character-count estimates suggest. Overestimate by 20–30%, or measure with a test compile.

## Files in this skill

- [`SKILL.md`](SKILL.md) — the operational checklist Claude follows when you invoke `/tikz`. Slimmed to delegate formulas to `tikz_rules.md`.
- [`tikz_rules.md`](tikz_rules.md) — the canonical formula reference (every pass, every clearance, every worked example). **Also read by `/beautiful_deck` Step 4.4** as its generation-time rule book — single source of truth shared between the two skills.

## Dependency note

`/tikz` and `/beautiful_deck` share the rule book in this folder. If you install `/beautiful_deck` without `/tikz`, Step 4.4 will fail to find `tikz_rules.md`. Install both, or update the path reference in `beautiful_deck/SKILL.md`.

## Related skills

- **`/beautiful_deck`** — invokes `/tikz` automatically as part of the visual cleanup step during end-to-end deck creation. Also reads `tikz_rules.md` from this folder for generation-time prevention (Step 4.4).
- **`/referee2`** (deck mode) — reads `tikz_rules.md` from this folder for margin and curve-clearance rules during slide audits.

## The philosophy

The common failure mode in academic decks is not "I couldn't make this figure" — it's "the figure compiles, looks mostly right, and has one subtle overlap that distracts the audience every time they look at it." Those overlaps are invisible to LaTeX and invisible to the author because they've stared at the diagram for hours.

`/tikz` was originally written as the sole defense against these overlaps. Experience showed that a repair-only approach is insufficient — Claude reads the formulas and *simulates* having done the calculation, but doesn't always execute them rigorously. The breakthrough was recognizing that **prevention is worth ten repair passes**: writing safe TikZ from the start (explicit dimensions, coordinate maps, no `scale`) eliminates most collision classes before `/tikz` ever runs.

The current architecture reflects this: `/beautiful_deck` Step 4.4 is the upstream defense (using the same `tikz_rules.md` reference). `/tikz` is the downstream check. Together they catch what either alone would miss.
