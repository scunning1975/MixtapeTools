# Beautiful Deck (`/beautiful_deck`)

> **End-to-end beautiful deck creation, from blank slate to audited, compiled PDF with accompanying scripts for students.**

`/beautiful_deck` is the operational version of the deck-generation prompt that used to live at [`presentations/deck_generation_prompt.md`](../../presentations/). Rather than re-pasting the prompt each time, invoke the skill.

---

## What it does

`/beautiful_deck` is the full pipeline:

1. **Triage** — gathers the audience, content source, aesthetic path, code language, output format, and one-sentence takeaway before touching any slides.
2. **Design an original theme** — builds a custom `.sty` or preamble tuned to the audience. Never boilerplate. A reader should not be able to guess what theme package is underneath.
3. **Design the narrative arc** — writes a one-page outline enforcing the pedagogical movement `Narrative → Application → Picture → Codeblock → Technical`. Shows the outline to the user for approval before writing any slides.
4. **Generate figures and tables code-first** — writes standalone R / Python / Stata scripts, runs them, saves figures and tables, and only then writes the `\includegraphics{}` and `\input{}` calls in the deck.
5. **Write the slides** — one idea per slide, assertion titles that normally fit on one line, no wall of sentences, MB/MC equivalence across the deck, and **safe TikZ generation from the start** (Step 4.4 — see below).
6. **Compile and fix warnings** — runs the compile loop until `Overfull`, `Underfull`, font, and fatal errors all return zero counts.
7. **Run `/tikz`** — invokes the measurement-based visual collision audit to catch any *residual* TikZ collisions. Because Step 5 writes safe TikZ from the start, `/tikz` is a check, not a rescue mission.
8. **Rhetoric audit (second agent)** — dispatches a sub-agent to verify titles-are-assertions, one-idea-per-slide, MB/MC balance, narrative arc, Devil's Advocate presence, and audience fit.
9. **Graphics audit (third agent)** — dispatches a second sub-agent focused only on numerical accuracy of figures/tables, label positioning, axis coherence, color consistency, and font sizing.
10. **Final compile** — recompiles to a clean state and delivers.

The skill also reads [`style_preferences.md`](style_preferences.md) for user-specific stylistic defaults. These are separate from the rhetorical principles in `rhetoric_of_decks.md`: rhetoric decides what the deck must accomplish; style preferences capture durable visual tastes that should carry across decks when they fit the audience and content. The file is currently populated with an example preference for reference; keep, edit, or delete it at the user's discretion.

The included [`preamble_warm_professional.tex`](preamble_warm_professional.tex) is Scott's house style for outward-facing academic decks. It is useful as an opt-in reference preamble, but it should not anchor the palette or layout of original audience-specific designs unless the user asks for that house style.

## Audience first — the load-bearing decision

The very first thing the skill resolves is **who the audience is**. Audience determines the rhetorical balance, the aesthetic direction, the act proportions, and the pacing — every other decision in the skill depends on it. The skill will not proceed to source-content discussion, theme work, or anything else until audience is committed.

The 5 canonical audience buckets:

| Bucket | What it means |
|---|---|
| **Academic seminar** | PhD-level research talk, methods-aware audience |
| **Teaching lecture** | Undergrad or grad course, clarity-first |
| **Conference presentation** | 20-min talk, fast punch, headline-result-on-slide-2 |
| **Working deck** | For coauthors, lab meetings, or future-self; rigor over polish |
| **External non-academic** | Policy, media, industry — high pathos, minimal jargon |

Provide audience in the invocation when you can. Examples:

```
/beautiful_deck "academic seminar" path/to/paper.pdf
/beautiful_deck "teaching lecture" path/to/lecture_notes.md
/beautiful_deck "external non-academic — policy briefing" "30-min talk on the CBS continuous DiD paper"
```

If audience is missing the skill will ask immediately (via a structured picker if available) before doing anything else. Free-text audience descriptions ("my advisor and one coauthor") are accepted — the skill maps them to the closest canonical bucket and confirms with you before proceeding. The "external non-academic" bucket has one follow-up sub-specifier (general public / policy / industry) because the rhetorical spread within that bucket is wider than within any other.

## Why the pedagogical movement matters

The single most important rule in this skill is the ordering:

**Narrative → Application → Picture → Codeblock → Technical**

Every section, every slide sequence, every topic must move in this order. Not the reverse.

The anti-pattern is the lecture that opens with definitions, proves a theorem, and then offers an example at the end "for intuition." That treats technical content as primary and intuition as decorative. Scott's pedagogy is the opposite: the intuition *is* the content, and the technical statement is what the audience walks *away* with, not what they walk in with.

The skill enforces this at every slide-sequencing step. If the agent catches itself writing a technical slide before the picture that motivates it, it backs up and writes the picture first.

## Why title line discipline matters

Slide titles are assertions, but they are still slide titles. A title that wraps is usually doing body-text work and can collide with frame-title ornaments, progress rules, or the slide body. The skill now treats one-line assertion titles as the default: rewrite shorter first, split the slide if needed, and avoid breaking words across lines whenever possible. The same no-broken-words rule applies to microtext in TikZ nodes, table cells, callout boxes, captions, and placeholders.

## Why an original theme matters

Aristotle's principle of **ethos** (credibility) is partially visual. An audience that sees a default Beamer theme in the first five seconds has already scored the speaker lower on preparation and care. An original, audience-tuned aesthetic earns back the attention budget before the first content slide arrives.

The skill requires:

- **Beamer default** — a custom `.sty` file or inline preamble fully styled.
- **Theme packages as foundation, not as identity** — you may build on top of `metropolis`, `moloch`, `focus`, `beamerposter`, etc. for sane spacing defaults, but you MUST override colors, fonts, frame-title style, title slide, and bullets enough that the result is visually unrecognizable as the source theme.
- **No defaults shipped** — under no circumstances should the deck land in Scott's hands with boilerplate styling.

For alternative formats (Quarto, reveal.js, Typst), the same rule applies — custom CSS, custom style blocks, overridden defaults.

## TikZ Generation Defaults (Step 4.4) — Prevention Over Repair

This is the most consequential addition to the skill. Previously, `/beautiful_deck` generated TikZ however it liked — autosized nodes, edge labels without directional keywords, no coordinate planning — and relied on `/tikz` (Step 7) to repair the collisions afterward. That pipeline was broken: `/tikz` is a repair tool, not a safety net, and it cannot reliably fix diagrams that were never built with measurement in mind.

Step 4.4 fixes this upstream. Every TikZ diagram generated by `/beautiful_deck` now follows five rules:

| Rule | What it prevents |
|---|---|
| **1. Explicit node dimensions** — every `\node` declares `minimum width` and `minimum height` | Autosized boxes make arrow endpoints unpredictable; downstream collisions become unfixable |
| **2. Directional keywords on every edge label** — `above`, `below`, `left`, `right`, `sloped`, `anchor=`, `pos=`, or `midway` required | Labels without keywords render ON the arrow line |
| **3. Coordinate map comment** before every `tikzpicture` — a commented block listing every node name, its coordinates, and intended dimensions | Forces spatial planning before drawing; makes `/tikz` audit passes faster and more reliable |
| **4. Canonical templates** for DAGs, flow charts, and RDD threshold diagrams | Known-safe skeletons instead of ad-hoc generation |
| **5. Never use `scale` on a complex diagram** | `scale` shrinks coordinates but not text, creating invisible collisions where the math looks correct but the rendered output is broken. Redesign at the intended size instead. |
| **6. Never define parameterized styles inside a Beamer frame** | `#1` inside a frame body is consumed by Beamer's argument parser before TikZ sees it, causing "Illegal parameter number" errors that cascade and resist all downstream fixes. Define all parameterized styles in the preamble with `\tikzset{}`. |

**Why Rule 5 matters especially.** The `scale=0.55` pattern — shrinking a large TikZ figure to fit a Beamer column — was the #1 source of label collisions in Scott's decks. The TikZ coordinates compress but font sizes do not, so a label that "should" be 1.5 units from another label is actually only 0.8 cm away, and the text is still rendered at native size. The collision is invisible in the source code and invisible to `/tikz` unless it compensates for the scale factor (which it often fails to do). Rule 5 eliminates the entire failure class by forbidding the pattern.

**The pipeline is now: prevention (Step 4.4) → compile (Step 5) → residual repair (Step 7, `/tikz`).** Most collisions should never be generated in the first place.

### The circuit breaker (Step 5)

If the same compile error persists after 3 different fix attempts, **stop editing and tell the user.** Quote the error, list what you tried, and ask how to proceed. The cost of asking is 2 minutes. The cost of spiraling is an hour of edits that make the file progressively worse. Every failed fix introduces new problems that obscure the original error. This rule overrides "recompile until clean" — zero tolerance for warnings does not mean infinite attempts.

## The Three Laws (inherited from Rhetoric of Decks)

1. **Beauty is function.** Beauty in presentation is clarity made visible. Decoration without function is noise.
2. **Cognitive load is the enemy.** One idea per slide. Two max for inseparable contrasts.
3. **The slide serves the spoken word.** If your slides can be understood without you speaking, you have written a document and called it a presentation.

## The Aristotelian triad

The rhetorical balance changes with audience. The skill's triage step (Q1) commits to a specific balance before any slides are written.

| Audience | Logos | Ethos | Pathos |
|---|---|---|---|
| Academic seminar (PhD-level, research talk) | 50% | 40% | 10% |
| Teaching lecture | 45% | 20% | 35% |
| Conference presentation (20 min) | 50% | 35% | 15% |
| Working deck (coauthors / future self) | 60% | 30% | 10% |
| External non-academic (policy, media, industry) | 30% | 25% | 45% |

## Usage

```
/beautiful_deck
```

with optional argument pointing to content:

```
/beautiful_deck path/to/lecture_notes.md
/beautiful_deck "restructure the deck in decks/2024_seminar/ for an undergraduate audience"
/beautiful_deck "a 20-minute conference presentation on the CBS continuous DiD paper, aimed at applied microeconomists"
```

The skill will ask clarifying questions if anything in the triage step is missing.

## Output structure

```
<deck_name>/
├── <deck_name>.tex          # Main Beamer source (or .qmd / .typ / .html for alternative formats)
├── <deck_name>.pdf          # Compiled deck (clean)
├── <deck_name>_outline.md   # The approved outline
├── preamble.tex             # If the preamble is factored out
├── scripts/
│   ├── figure_1.R           # Standalone, runnable by students
│   └── ...
├── figures/
│   ├── figure_1.pdf
│   └── ...
└── tables/
    ├── table_1.tex          # LaTeX fragment
    └── ...
```

## Dependencies

**`/beautiful_deck` depends on `/tikz` being installed.** Two specific dependencies:

1. **Step 4.4 (TikZ generation rules)** reads `~/.claude/skills/tikz/tikz_rules.md` for the canonical formula reference (gap calculations, Bézier curve depths, clearance tables). This file lives in the `tikz` skill folder so that both `/beautiful_deck` (generation-time) and `/tikz` (audit-time) read from a single source of truth.
2. **Step 6 (visual cleanup)** invokes `/tikz` directly to audit residual collisions after the slides are written.

If you install `/beautiful_deck` without `/tikz`, both steps will fail. Always install them as a pair.

## Related skills

- **`/tikz`** — the measurement-based TikZ collision audit. Invoked during the visual cleanup step. Required dependency (see above).
- **`/referee2`** — the full five-audit protocol. `/beautiful_deck` uses a rhetoric-scoped variant of it in the audit step.
- **`/split-pdf`** — if the source content is a paper Scott is reading, split it first and work from the summaries.

## The philosophy behind it

Full essays (in this skill directory):
- [`rhetoric_of_decks.md`](rhetoric_of_decks.md) — the operational principles
- [`rhetoric_of_decks_full_essay.md`](rhetoric_of_decks_full_essay.md) — the 600-line intellectual genealogy from Aristotle through LLMs
- [`style_preferences.md`](style_preferences.md) — user-specific stylistic defaults, including functional slide-header progress indicators.

`/beautiful_deck` is the operational skill version of those essays. You don't need to re-read them to invoke it — the skill handles the workflow — but the essays explain *why* the principles work.
