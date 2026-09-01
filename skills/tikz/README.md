# TikZ Collision Audit (`/tikz`)

> **A repair tool for residual TikZ collisions — not a safety net for bad generation.**

`/tikz` catches what `pdflatex` doesn't: labels sitting on arrows, text bleeding into box edges, Bézier curves passing through other labels, arrows pointing to the wrong node. LaTeX reports none of these. Humans usually miss them on first review. `/tikz` finds them by computing the actual geometry.

## The critical distinction: prevention vs. repair

**`/tikz` is a repair tool.** It runs measurement-based checks on existing TikZ code and fixes what it finds. But it cannot reliably fix diagrams that were never built with measurement in mind — autosized nodes, missing directional keywords, `scale` factors that compress coordinates but not text. These upstream generation problems produce collisions that are structurally unfixable by any audit pass.

**The upstream defense is `/beautiful_deck` Step 4.4**, which writes safe TikZ from the start: explicit node dimensions, coordinate maps, directional keywords on every edge label, canonical templates for common diagram types, and a strict prohibition on `scale` for complex diagrams. When Step 4.4 does its job, `/tikz` has little to find. When Step 4.4 is skipped — or when you're auditing TikZ that was written outside of `/beautiful_deck` — `/tikz` does its best, but the success rate depends entirely on how the TikZ was generated.

**The pipeline**: prevention (Step 4.4) → compile (Step 6) → residual repair (`/tikz`, Step 7).

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

`/tikz` runs a fixed, ordered protocol. Each pass targets a specific class of collision.

| Pass | What it checks |
|---|---|
| **Pass 0** | **Cross-slide consistency** — when the same diagram appears on multiple frames, colors, positions, and font sizes must be identical except for the deliberate change (a new highlight, a new node revealed). |
| **Pass 1** | **Bézier curves first.** Every `bend` in the file. Computes the maximum curve depth from the chord length and bend angle, adds a 0.5cm safety margin, and checks every label in the danger zone. Also checks for curves crossing other arrows. |
| **Pass 2** | **Edge label gap calculations.** For every label placed between two nodes, estimates the label's width in cm (from character count and font size), compares to the usable gap, and flags any case where width exceeds the gap. Most common fix: break the label out as a standalone `\node` above the arrow midpoint. |
| **Pass 3** | **Arrow label positioning keywords.** Every `node[...]{}` on an arrow must carry `above`, `below`, `left`, `right`, `anchor=`, `pos=`, or `midway`. Anything missing sits ON the arrow line. Greps for violations. |
| **Pass 4** | **Boundary Rule.** For every drawn shape, computes the boundary and flags any label within 0.4cm of it. Also applies to matplotlib / ggplot2 patches and `FancyBboxPatch` objects — the same rule. |
| **Pass 5** | **Margin check.** Minimum clearances: label ↔ label 0.3cm; label ↔ axis 0.3cm; label ↔ arrow 0.3cm; arrow origin ↔ box edge 0.15cm; label ↔ shape boundary 0.4cm; any object ↔ slide edge 0.5cm. |

A final **Pass 6** opens the PDF and asks for a visual sanity check — trust the math, then trust your eyes.

## Minimum clearances

These are the measurements the skill enforces. Everything the pdflatex log cannot see, but everything an attentive reader does see:

| Pair | Minimum clearance |
|---|---|
| Label ↔ label | 0.3 cm |
| Label ↔ axis line | 0.3 cm |
| Label ↔ arrow | 0.3 cm |
| Arrow origin ↔ box edge | 0.15 cm |
| Label ↔ shape boundary (circle, rectangle, fill) | 0.4 cm |
| Any object ↔ slide edge | 0.5 cm |

## Font-to-width reference (for gap calculations)

Text width estimation in Pass 2:

| Font | Width per character |
|---|---|
| `\scriptsize` | 0.10 cm |
| `\footnotesize` | 0.12 cm |
| `\small` | 0.15 cm |
| `\normalsize` | 0.18 cm |
| Bold | +10% |

## The bend-angle → curve-depth table

For Pass 1 Bézier calculations: `max_depth = (chord_length / 2) × tan(bend / 2)`.

| Bend angle | tan(angle/2) |
|---|---|
| 20° | 0.176 |
| 25° | 0.222 |
| 30° | 0.268 |
| 35° | 0.315 |
| 40° | 0.364 |
| 45° | 0.414 |

## The re-audit rule

**One collision fix almost always reveals another one.** After any change, `/tikz` re-runs Passes 1–5 on *all* TikZ figures in the file, not just the one that was touched. Moving a label to fix one collision can push it into another node, or reveal a previously hidden overlap on a nearby arrow. The skill treats the audit as complete only when a full pass on the entire file returns zero violations *and* a subsequent `pdflatex` shows zero Overfull, Underfull, or font warnings.

## Common patterns and fast fixes

Catalog of the collision patterns Scott has seen most often in his own decks:

| Pattern | Symptom | Fix |
|---|---|---|
| Label between wide boxes | Text bleeds into box edge | Move label above the arrow as a standalone `\node` |
| "Step 1" / "Step 2" labels on flow diagrams | Labels overlap box text | Place labels *above* the arrow band, not as edge labels |
| Diagonal arrow label at `below right` | Label lands inside another box | Use `pos=0.55` and compute the landing position |
| Return curve crossing a vertical arrow | Arrows intersect visually | Reverse bend direction (`bend left` ↔ `bend right`) |
| `scale=0.8` used on a complex diagram | Text is large, gaps are small | Redesign at the intended size; avoid `scale` on complex figures |
| Slope label on a regression line | Label sits on top of the line | Use `node[anchor=west]` at a point 0.3cm off the line end |
| `\\` inside `\textcolor{}` | Hbox overflow | Break into two separate `\textcolor` calls on separate lines |

## Usage

```
/tikz path/to/deck.tex
```

`/tikz` will identify every `tikzpicture` environment in the file, run the six passes on each, and produce a report with exact line numbers for every violation. It applies fixes directly to the source file, then recompiles to verify.

## When to use it

- **Always after `/beautiful_deck`** — the skill invokes `/tikz` automatically as part of the visual cleanup step (Step 7). Because Step 4.4 now writes safe TikZ from the start, `/tikz` should find few or no issues in new decks. Re-run manually after any significant edit to a diagram.
- **After any TikZ edit** — adding a new node, changing a bend angle, repositioning a label. Don't trust visual inspection alone; run the math.
- **Before shipping a deck** — final pre-flight check after the deck compiles cleanly.
- **When a diagram "looks wrong" but you can't say why** — `/tikz` will find the exact measurement causing the discomfort.
- **On TikZ written outside of `/beautiful_deck`** — legacy diagrams, inherited decks, or hand-written TikZ. These are the cases where `/tikz` works hardest, because the upstream prevention rules (Step 4.4) were not applied. Expect more findings and more iteration.

## Known limitations

- **Cannot fix autosized nodes reliably.** If a `\node` has no explicit `minimum width`/`minimum height`, its rendered dimensions depend on the text content and font — information `/tikz` can only estimate, not compute exactly. The fix is upstream: write explicit dimensions (Step 4.4, Rule 1).
- **`scale` factor creates invisible collisions.** `scale=0.55` shrinks coordinates but not text. `/tikz` attempts to compensate, but the compensated gap calculations are less reliable than diagrams drawn at intended size. The fix is upstream: never use `scale` on complex diagrams (Step 4.4, Rule 5).
- **Pass 6 (visual sanity check) is unreliable.** Claude cannot reliably inspect rendered PDFs at the pixel level. Passes 1–5 (measurement-based) are the real defense. Pass 6 is a belt-and-suspenders reminder, not a guarantee.

## Related skills

- **`/beautiful_deck`** — invokes `/tikz` automatically as part of the visual cleanup step during end-to-end deck creation, and reads this skill's `tikz_rules.md` during Step 4.4 to prevent collisions before they are generated.

## The philosophy

The common failure mode in academic decks is not "I couldn't make this figure" — it's "the figure compiles, looks mostly right, and has one subtle overlap that distracts the audience every time they look at it." Those overlaps are invisible to LaTeX and invisible to the author because they've stared at the diagram for hours.

`/tikz` was originally written as the sole defense against these overlaps. Experience showed that a repair-only approach is insufficient — Claude reads the formulas and *simulates* having done the calculation, but doesn't always execute them rigorously. The breakthrough was recognizing that **prevention is worth ten repair passes**: writing safe TikZ from the start (explicit dimensions, coordinate maps, no `scale`) eliminates most collision classes before `/tikz` ever runs.

The current architecture reflects this: `/beautiful_deck` Step 4.4 is the upstream defense, using the same `tikz_rules.md` reference that `/tikz` reads during repair. `/tikz` is the downstream check. Together they catch what either alone would miss. Every collision rule in `/tikz` has a formula behind it. Every formula was written down because a prior version of a Scott deck had exactly that collision, found only after the audience saw it. The skill is the accumulated scar tissue of previous deck-polishing sessions — now paired with generation rules that prevent the same scars from forming in the first place.

## Full reference

The canonical formula reference:
- [`.claude/skills/tikz/tikz_rules.md`](../../.claude/skills/tikz/tikz_rules.md) — every formula, every clearance, every worked example
- [`.claude/skills/tikz/SKILL.md`](../../.claude/skills/tikz/SKILL.md) — the operational checklist Claude follows when you invoke `/tikz`
