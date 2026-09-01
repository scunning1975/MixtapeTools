---
name: beautiful_deck
description: >-
  End-to-end beautiful Beamer deck creation. Designs an original Beamer theme
  tailored to a specific audience, restructures existing content via the
  Rhetoric of Decks (ethos / pathos / logos), generates figures and tables from
  R/Python/Stata code first, embeds code blocks in the deck, produces standalone
  walkthrough scripts, compiles to zero warnings, runs /tikz for visual
  collision cleanup, and dispatches a graphics-only audit agent for label and
  coordinate checks. Use when creating a presentation from scratch or
  restructuring existing content into a new beautiful deck.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Task
argument-hint: "[audience] [content-path-or-description]"
---

# Beautiful Deck

This skill implements Scott's full deck-creation pipeline. It is NOT just a compile helper — it is the entire workflow from blank slate to audited, compiled PDF with accompanying scripts for students.

Scott's philosophy: **a deck is a performance medium, not a document**. It must be beautiful, technically rigorous, smoothly paced (MB/MC equivalence across slides), and visually clean at the pixel level. Every element earns its presence. Every title is an assertion. Every figure carries one message.

This skill is the orchestrator. It calls `/tikz` for visual cleanup, draws on its own local reference files (preambles, palettes, TikZ measurement formulas, domain patterns, style preferences) in this skill directory, and dispatches sub-agents for rhetoric and graphics audits.

---

## Step 0: Triage — Gather Context Before Touching Anything

You MUST collect answers to these questions before generating a single slide. If the user hasn't provided them in the invocation, ask explicitly. Do not guess.

### Q1: Who is the audience? (**HARD BLOCK — resolve before any other question**)

Audience is the single decision that ripples through every other choice in this skill — the rhetorical balance, the aesthetic direction, the act proportions, the pedagogical pacing all depend on it. Resolve audience first; do not proceed to Q2 (source content), theme design, or anything else until audience is committed.

**If audience is missing from the invocation, ask immediately.** Use the `AskUserQuestion` tool (if available) to present a structured picker with the 5 canonical buckets as choices plus "Other." If `AskUserQuestion` is not available, ask in plain text and present the 5 canonical buckets as a numbered list. Do not begin theme work, source-content discussion, or anything else until the user has answered.

The 5 canonical buckets (cite this table verbatim when confirming with the user):

| Context | Logos | Ethos | Pathos | Implications for the deck |
|---|---|---|---|---|
| **Academic seminar (PhD-level, research talk)** | 50% | 40% | 10% | Sparse, performative, identification strategy early, one coefficient at a time, Devil's Advocate slide |
| **Teaching lecture (undergrad or grad course)** | 45% | 20% | 35% | Clarity > compression, progressive revelation, worked examples as content, recap slides allowed |
| **Conference presentation (20 min talk)** | 50% | 35% | 15% | Fast punch, headline result on slide 2, no literature review, ~15 slides max |
| **Working deck (for coauthors or future-self)** | 60% | 30% | 10% | Document choices, preserve uncertainty, more text allowed, rigor > polish |
| **External non-academic (policy, media, industry)** | 30% | 25% | 45% | Storytelling, human impact, minimal jargon, visual impact |

**If the user gives free-text audience description (or picks "Other"), map to the closest canonical bucket and confirm with the user before proceeding.** Use this mapping table as a guide:

| Free-text the user might give | Maps to |
|---|---|
| "my advisor and one coauthor" | Working deck |
| "intro economics class" / "undergrad lecture" | Teaching lecture |
| "general public" / "media interview" | External non-academic |
| "internal team" / "lab meeting" / "future-self" | Working deck |
| "policy briefing" / "congressional staff" | External non-academic |
| "NBER conference" / "AEA session" | Conference presentation |
| "job market talk" / "research seminar" | Academic seminar |

When confirming the mapping, be explicit: "Mapping your description '<user's free text>' to **<canonical bucket>** — does that match what you have in mind?"

**Sub-specifier for External non-academic.** When the user picks (or maps to) external non-academic, the rhetorical spread within this bucket is wider than within any other bucket. Ask one follow-up before proceeding:

> External non-academic — which sub-context?
> - **General public / media** (maximum pathos, story-driven, minimum jargon)
> - **Policy / government / advocacy** (evidence-driven, action-oriented, moderate jargon)
> - **Industry / corporate** (decision-oriented, ROI framing, domain jargon OK)

Why this bucket only: the other 4 buckets have natural sub-variants (undergrad vs. grad teaching; methods vs. applied seminar) but the rhetorical mix stays largely the same. External is the unique case where the *kind* of pathos shifts, not just the dose.

### Q2: What is the source content?
- A paper draft (`.tex`, `.pdf`, `.md`)
- Existing lecture notes
- An existing deck to be restructured
- A description and you generate from scratch
- A paper the user is reading (in which case: have they split-pdf'd it? If yes, read the summaries. If no, ask whether to split-pdf first.)

### Q3: What is the tone / aesthetic?

Two paths. Pick ONE:

**Path A: Scott's house style (Professional/Academic).** Use `~/.claude/skills/beautiful_deck/preamble_warm_professional.tex`. This is a ready-to-copy house-style preamble for outward-facing academic work, not a default palette for every deck.

**Path B: Original, audience-specific design.** You design something new — a palette, a frame-title style, a TikZ accent system — tuned to this specific audience. This is the default when Scott says "design for me an original Beamer style." Do NOT reuse a previous deck's theme. You are creating something new.

### Q4: Which code language for figures and tables?
R (ggplot2 + xtable/kable), Python (matplotlib/seaborn + pandas to LaTeX), or Stata (graph export png + esttab). Pick ONE for the whole deck.

### Q5: Output format — Beamer (default) or something else?

**The default is always Beamer.** Do not switch formats unless the user explicitly asks. This is an opinionated choice: Beamer gives the richest control over typography, TikZ, math typesetting, and precise layout — and it compiles to a single PDF that projects reliably anywhere.

The user may request an alternative markdown-based presentation system. Accept these on explicit request:

- **Quarto (`.qmd` → HTML / reveal.js or PDF / Beamer)** — accepted if the user says "Quarto" or "reveal.js". Produces HTML slides with live code execution, good for live coding demos.
- **R Markdown (`.Rmd` → xaringan or ioslides)** — accepted if the user specifies. Mostly superseded by Quarto.
- **Typst** — accepted if the user specifies. Newer, faster compiles, less mature ecosystem.
- **Raw HTML / reveal.js** — accepted if the user specifies. Full web control, needs a browser to present.
- **Pure markdown → Marp** — accepted if the user specifies. Lightweight, limited typographic control.

Whichever format is chosen, the Three Laws and the Aristotelian balance are unchanged. The format is the medium; the rhetoric is the substance. Everything in the rest of this skill applies — one idea per slide, assertion titles, MB/MC equivalence, code-first figure generation, the rhetoric and graphics audits. Only the specific compile commands and preamble syntax change.

For alternative formats, you still produce the same outline (Step 2), the same code-first scripts (Step 3), the same rhetoric audit (Step 7), and the same graphics audit (Step 8). The preamble becomes a Quarto YAML header, a Typst style block, or a reveal.js CSS file instead of a Beamer `.sty`, but the design principles below still apply.

**Ask the user once at the start: "Beamer (default) or another format?" If they don't answer or answer unclearly, use Beamer.**

### Q6: What is the ONE sentence the audience should remember?
This goes on the closing slide and frames the entire narrative arc. If the user can't state it in one sentence, help them find it before you write any slides.

---

## Step 1: Design the Theme — Original, Not Boilerplate

### The non-negotiable rule

**Whatever format the user chose in Q5, the visual design must be original to this deck.** Not a reused template. Not a default Beamer theme the audience has seen a hundred times. A reader looking at the compiled PDF should NOT be able to guess what theme package is underneath.

This is the rule regardless of the format:
- **Beamer:** You must produce a custom `.sty` file or an inline preamble that is fully styled. You MAY build on top of a theme package like `metropolis`, `beamerposter`, `moloch`, or `focus` as a foundation — they give you sane defaults for spacing and structure — but you MUST override the colors, fonts, frame-title style, title slide, and bullets enough that the result is visually unrecognizable as the source theme. A reader should see a Scott-original aesthetic, not "oh, metropolis again."
- **Quarto / reveal.js:** Custom CSS, custom theme file, overridden defaults. Do not ship the default Quarto theme.
- **Typst:** Custom style block with real design choices, not the default.

Under no circumstances ship boilerplate. The effectiveness of the deck comes from **a visual identity tuned to this specific content and this specific audience**, per Aristotle's principles of ethos, pathos, and logos. Boilerplate signals "I didn't bother" — which destroys ethos before the first slide lands.

The goal is: something truly effective for *this* audience, *this* content, and the rhetorical balance you committed to in Q2. If the audience is undergraduate data science, the aesthetic should feel different from a PhD causal inference seminar. If the audience is a policy audience, it should feel different from a conference theory talk. The palette, the typography, the frame-title treatment, the section dividers — every element should be chosen deliberately.

### How to approach it

**If Path A (Scott's house style):** Copy the Warm Professional preamble from `~/.claude/skills/beautiful_deck/preamble_warm_professional.tex` — this IS Scott's house style and is not boilerplate for outward-facing academic work. Proceed to Step 2. Do not use this file as inspiration for Path B unless the user explicitly asks for a deck in that house style.

**If Path B (original design — the default when Scott says "design for me an original Beamer style"):** You are designing an original aesthetic. Follow this process:

Before implementing either path, read `~/.claude/skills/beautiful_deck/style_preferences.md`. Treat it as user-specific stylistic guidance only: it should shape persistent visual preferences such as slide-header treatments, but it does not override audience fit, content needs, or the rhetorical principles in `rhetoric_of_decks.md`.

### 1.1 Palette construction

Pick a core accent (one color, not an ensemble). This is the emotional anchor of the deck. The examples below illustrate audience-to-color reasoning; they are not a house palette to reuse by default.

| Audience | Core accent | Why |
|---|---|---|
| Undergraduate data science | Teal #048A81 | Fresh, energetic, reads as "modern" without being juvenile |
| PhD causal inference seminar | DeepNavy #2E4057 | Serious, anchored, matches the rhetorical weight of identification |
| Policy / applied work | WarmOrange #E85D04 | Human warmth, urgency, signals "this matters" |
| Conference theory talk | SoftPurple #9D4EDD | Distinctive, academic, unusual enough to be remembered |

Around the core, build a 10-color palette: 1 core accent, 1 secondary accent (analogous or complementary), 2 neutrals for text (one dark, one warm gray), 2 background neutrals (cream + white), 1 alert color (usually a deep red), 1 success / positive color (usually forest green or teal), 2 tertiary colors for charts. Define them all in `\definecolor{}` at the top of the preamble.

Use https://www.viget.com/articles/color-contrast/ as a WCAG-AA reference — all body text must have contrast ratio ≥ 4.5:1 against background.

### 1.2 Frame-title style

Pick ONE visual treatment for frame titles. Options that read well:
- **Left rule:** a thin colored vertical bar to the left of the title (2mm wide, core accent color)
- **Underline:** a 1pt horizontal rule below the title in core accent
- **Background tint:** a very light tint of the core accent behind the title area
- **Simple bold:** no decoration, just bold dark text with generous white space

Do NOT combine multiple. Pick one and use it consistently.

### 1.3 Bullet style

If bullets appear at all, use a single `\tikz\fill` circle in the core accent, sized to match the text baseline. Subitems get a smaller circle in the secondary accent. No standard Beamer triangles, no arrows, no squares.

### 1.4 Section dividers

Full-bleed dark background (core accent or a dark neutral), white text, one large label centered. Use `\transitionslide{Title}{Subtitle}` pattern defined in `preamble_warm_professional.tex`. This creates the "deck breathes" rhythm — a moment of rest between sections.

### 1.5 Typography

- `\usefonttheme{professionalfonts}` — required.
- Body text: 24pt minimum. Title: `\huge`. Frame title: `\Large\bfseries`. Footnote floor: 18pt.
- Sans-serif. If you want a custom font, use one already installed: `lmodern` (default), `roboto`, `fira`, or `utopia`. Do NOT require the user to install fonts.
- Never justify text. Always ragged right (`\RaggedRight`).

### 1.6 Write the preamble

Output the full preamble to `<deck_name>.tex`. Include every package needed, every color, every beamer color assignment, every font setup, and the `\transitionslide` macro. The preamble is boring but load-bearing — get it right on the first pass so you don't have to revisit.

---

## Step 2: Design the Narrative Arc

Before writing any slides, write a **one-page outline** in a `<deck_name>_outline.md` file. Show it to the user before proceeding to slide generation. This is the checkpoint where the user can course-correct cheaply.

### The pedagogical movement — intuition first, technical last

**This is the single most important rhetorical commitment in this skill.** Every topic, every section, every slide sequence must move in the following order:

**Narrative → Application → Picture → Codeblock → Technical**

Not the reverse. Never the reverse.

| Stage | What it looks like | Why it comes here |
|---|---|---|
| **1. Narrative** | A story, a concrete scene, a named person in a named place facing a real problem. "In 2001, Chinese hospitals faced a policy change that forced them to cut labor subsidies..." | Anchors the audience in something human and specific before anything abstract arrives. Activates pathos. Builds curiosity, not resistance. |
| **2. Application** | A specific example the audience can hold in their hand. "Suppose you are a hospital manager deciding whether to hire a nurse or buy an MRI machine." | Makes the abstraction physical. The audience can *picture* the decision, not just parse the symbols. |
| **3. Picture** | A figure, a diagram, a visual that shows the pattern. One message per picture. Labeled directly. | Pictures carry intuition faster than words or equations. The audience sees the relationship before they name it. |
| **4. Codeblock** | A short, readable snippet that shows how the idea is computed. Embedded in the deck, matching the deck's palette, also saved as a standalone script. | Code is a concrete, operational form of the idea. It is a middle layer between intuition and formalism — more precise than a picture, more approachable than a theorem. |
| **5. Technical** | The equation. The theorem. The identification strategy in formal notation. The proof. | This arrives AFTER the audience already understands what it is saying. The technical statement becomes a compact summary of what they have already intuited — not a wall they must climb. |

**The anti-pattern is the lecture that opens with definitions, proves a theorem, and then offers an example at the end "for intuition."** This treats the technical as primary and the intuition as decorative. Scott's pedagogy is the opposite: the intuition is the content, and the technical statement is what you walk AWAY with, not what you walk IN with.

When sequencing a section, check every transition: am I moving toward the technical, not away from it? If you find yourself showing an equation before the figure that motivates it, swap them. If you find yourself writing "let $X$ be a random variable..." before the audience has a story to attach $X$ to, delete that slide and start with the story.

**Exceptions to the order:**
- **Definitions of load-bearing terms** may appear early if the term is unavoidably needed — but even then, state the intuitive meaning first in plain English, then give the formal definition on the *next* slide.
- **Roadmap slides** in long teaching decks can appear before the narrative begins (for orientation) — but the first *content* slide must still be narrative.
- **Title slides and section dividers** are structural and exempt.

### The arc structure

Every deck has three acts. The proportions depend on audience (see Q2 table).

**Act I — Tension (open + setup).** 2–4 slides.
- Title slide.
- Opening hook: a provocative question, a surprising statistic, or a concrete problem the audience recognizes. **NOT** an agenda, **NOT** "Today I'm going to talk about...", **NOT** a definition slide. See `rhetoric_of_decks.md` Part IV "The Opening" for examples.
- The stakes: why does this matter? (This is where pathos lives.)
- The roadmap (optional — only for teaching decks > 30 slides).

**Act II — Investigation (the argument).** 60–75% of the deck.
- Identification strategy early (for academic seminars — skeptics want to know your source of variation before they'll engage with results).
- One idea per slide. Pyramid principle within each section: state the sub-claim, then support it.
- Alternate: dense technical slides with lighter summary / figure slides. This creates the "deck breathes" rhythm.
- Devil's Advocate slide near the end of Act II (for academic or external decks): "A skeptic would say..." followed by the response.

**Act III — Resolution (takeaway).** 2–4 slides.
- The headline result, stated as a claim (title) with one figure or one equation supporting it.
- Implications: what does this change? What should the audience do or believe differently?
- Closing slide: the ONE sentence from Q5, on a full-bleed dark background, centered. **NOT** "Questions?", **NOT** "Thank you". This slide lingers — it is what people remember.

### Titles as assertions

Every slide title must state a claim. Examples:

| Weak (label) | Strong (assertion) |
|---|---|
| Results | Treatment increased K/L ratio by 18% on average |
| Identification | We exploit the 10% WTO tariff ceiling as a mechanical dose |
| Methodology | Markups are computed via De Loecker–Warzynski, not Cobb-Douglas |
| Literature | Prior work confuses level effects with causal responses |
| Implications | A smaller subsidy would have generated the same K/L response |

If someone reads only the titles in sequence, they should understand the entire argument. Test this: write out just the titles. Does the sequence tell a coherent story? If not, your arc is broken.

### Title length and line breaks

Assertion titles should normally fit on one line. A title that wraps is usually trying to do body-text work. Rewrite it shorter before adding title-template machinery.

Use this order:

1. Keep the assertion, but remove setup words.
2. Replace a clause with a sharper verb.
3. Move qualifiers into the visual, caption, speaker notes, or the next slide.
4. Split the slide if the full assertion needs multiple clauses.

When line breaks are unavoidable, break only between words whenever possible. Do not rely on hyphenating or splitting a word across lines to make a title or body text fit; rewrite, resize the specific element, or change the layout first.

This applies everywhere text appears, including TikZ nodes, table cells, callout boxes, captions, and screenshot placeholders. Short labels are especially sensitive: a two-word label such as "paper extraction" may wrap between words, but an ordinary word like "paper" or "sessions" must not be split across lines. If a word breaks inside a constrained box, widen the box or column, shorten the phrase, reduce only that local font size, or redesign the layout.

### The outline checkpoint

Write the outline as:
```
# <Deck name> — Outline

## Audience and rhetoric
<Copy the Q1–Q5 answers here>

## Theme
<Describe the palette, frame title style, aesthetic choices>

## The arc
### Act I (slides 1–4)
  1. Title
  2. Opening: <hook>
  3. Stakes: <why this matters>
  4. Roadmap (optional)

### Act II (slides 5–N)
  5. <Assertion title>
  6. <Assertion title>
  ...

### Act III (slides N+1 to end)
  ...
  K. Closing: <the one sentence>

## Figures and tables (code-first)
  - Figure 1: <what it shows, which script generates it>
  - Table 1: <what it contains, which script generates it>
```

**SHOW THIS OUTLINE TO THE USER AND WAIT FOR APPROVAL BEFORE WRITING SLIDES.** Do not skip this step. It is dramatically cheaper to fix the arc at this stage than after every slide is written.

---

## Step 3: Figure and Table Generation — Code First, Then Embed

This is the non-negotiable order:

1. Write standalone scripts FIRST, in `scripts/` subdirectory
2. Run them FIRST, generating figures into `figures/` and tables into `tables/`
3. Only THEN write the `\includegraphics{}` and `\input{}` calls in the deck

The reverse order — writing `\includegraphics{figure_1.png}` first and generating `figure_1.png` to match — is the #1 cause of mismatched labels, wrong data, and broken compiles. Do not do it.

### 3.1 Scripts must be standalone

Each script must run on its own without depending on other scripts. A student should be able to open `scripts/figure_3.R`, run it, and reproduce exactly `figures/figure_3.png`. This means:
- Absolute imports at the top
- Data loading at the top (from `data/` — do not hard-code absolute paths)
- Figure or table export at the bottom
- No shared state between scripts

### 3.2 Figure principles (applies to R, Python, or Stata)

- **One message per figure.** If you can't state the takeaway in one sentence, the figure is too complex.
- **Title states the finding** (not the chart type). "Markups fell fastest at the 95th percentile" not "Markup distribution over time".
- **Direct labels, no legends** whenever possible. Label the lines at their endpoints. Label the bars inside the bars. Reserve legends only for truly unreadable density.
- **Match the deck's palette.** Import the deck colors into the script so the figures read as part of the deck, not as foreign imports.
- **Figure background matches the slide background.** In matplotlib: `fig.set_facecolor()` and `ax.set_facecolor()`. In ggplot2: `theme(plot.background = element_rect(fill = ...))`.
- **Vector format (PDF) for line charts and schematics.** PNG only for images or dense rasters where vector files would be too large.
- **Check coordinates explicitly.** ggplot2 and matplotlib have silent failure modes where labels get cut off, legends obscure data, or tick marks misalign. The `/tikz` skill also checks figure label positioning — use it.

### 3.3 Table principles

- **Use `booktabs`** — no vertical rules, no double horizontal rules. Top rule, mid rule, bottom rule. Nothing else.
- **Highlight the key number.** A coefficient of interest should be boxed, colored, or bolded. Not all numbers are equal.
- **Strip everything that doesn't advance the argument.** Standard errors in parentheses, stars for significance, R² and N at the bottom. No "Adj R²", no "F-stat", no "Prob > F" unless the argument depends on them.
- **Export to `.tex` fragments, not full tables.** Use `\input{tables/main_result.tex}` in the deck, so the script can regenerate without touching the deck source.

### 3.4 Embed code blocks in the deck

When the deck teaches code (teaching decks, pedagogical content), show the code **in the deck** using a `listings` environment styled to match the palette. Example:

```latex
\begin{lstlisting}[basicstyle=\ttfamily\small,
                   keywordstyle=\color{DeepNavy}\bfseries,
                   commentstyle=\color{WarmGray}\itshape,
                   stringstyle=\color{Teal},
                   backgroundcolor=\color{Cream},
                   frame=single,
                   framesep=4pt,
                   rulecolor=\color{LightGray}]
df |>
  summarize(.by = sic3,
    Delta_ln_theil = ln_theil[year == 2004] - ln_theil[year == 2001],
    dose = pmax(tariff[year == 2001] - 0.1, 0)
  ) |>
  drop_na()
\end{lstlisting}
```

Keep code blocks short (< 12 lines). If the code is longer, split across slides or show a structural skeleton on the slide and put the full code in the accompanying script file.

**Scott's rule:** every code block shown in the deck should correspond to a real script file in `scripts/` that the user can hand to students. The deck is the performance; the script is the reference.

---

## Step 4: Write the Slides

Now, and only now, start writing slides.

### 4.1 The process

Work slide by slide, but also slide-sequence by slide-sequence. For each slide, and before moving to the next:

1. Re-read the outline to confirm this slide's role in the arc.
2. **Check the pedagogical movement within the section.** Where are we in the Narrative → Application → Picture → Codeblock → Technical sequence? If we are writing a technical slide, confirm that the preceding slides have already delivered the story, the application, the picture, and (if relevant) the code. If they have not, back up and write those slides first. Never let the technical arrive before the intuition.
3. Write the title as an assertion that fits on one line unless there is a deliberate exception.
4. Pick ONE visual element: a figure, an equation, a diagram, a single statistic, a code block. Not two.
5. Add minimal supporting text — a labeled setup ("From the FOC:", "Step 1:") or ONE concluding line. NEVER a wall of sentences.
6. Check: can someone in the back row read every character? If not, cut text or increase font.

### 4.2 The hard rules (no exceptions)

- **One idea per slide.** Two max for inseparable contrasts.
- **One-line assertion titles by default.** If a title wraps, rewrite it shorter before engineering around the wrap.
- **Do not split words across lines when avoidable.** Hyphenated or broken words are a last resort; prefer rewriting, resizing the specific element, or changing layout. This includes TikZ nodes and table cells, not just prose text.
- **No wall of sentences.** If you catch yourself writing a sentence that narrates what the audience can see, delete it.
- **No bullet lists by default.** Find the structure (sequence, contrast, hierarchy, causal chain) and make it visible with layout.
- **No decoration without function.** Stock photos, clip art, decorative icons — delete.
- **White space is confidence.** Crowded slides signal anxiety. Generous margins signal authority.
- **TikZ before figures.** When a diagram can be drawn in TikZ, prefer TikZ over imported graphics. You get vector quality, palette integration, and in-place editing.

### 4.3 MB/MC equivalence — the rhythm check

After drafting the full deck, walk through it and rate each slide's MB (marginal benefit) and MC (marginal cost) on a 1–5 scale. The optimal deck has the MB/MC ratio approximately equal across all slides. Look for:

- **Overloaded slides (MB/MC too low):** text in the footer, multiple competing ideas, charts with too many series. Split or simplify.
- **Underloaded slides (MB/MC too high):** a single word where a sentence would reinforce, wasted real estate. Add or merge.

**Exception: deliberate jump scares.** A sudden spike in density for rhetorical effect — a dense regression table, a provocative claim, a complex diagram. These must be INTENTIONAL. One or two per deck max.

### 4.4 TikZ Generation Defaults — Write Safe TikZ From the Start

These rules exist because `/tikz` (Step 6) is a repair tool, not a safety net. It can catch remaining collisions, but it cannot reliably fix diagrams that were never built with measurement in mind. Safe generation is the defense; `/tikz` is the check.

**Rule 1 — Always set explicit node dimensions.** Every `\node` must declare `minimum width` and `minimum height`. Never let TikZ autosize a box. Autosized boxes make arrow endpoints unpredictable and cause downstream collisions that `/tikz` cannot reliably repair. Example: `\node[draw, minimum width=3cm, minimum height=1cm] (A) {Label};`

**Rule 2 — Every edge label must carry a directional keyword.** Any `node[...]` placed on an arrow without `above`, `below`, `left`, `right`, `sloped`, `anchor=`, `pos=`, or `midway` will render ON the arrow line. This is never what you want. No exceptions.

**Rule 3 — Write a coordinate map comment before every tikzpicture.** Before the first `\node`, write a commented block listing every node name, its coordinates, and its intended dimensions. This forces spatial planning before drawing and makes `/tikz` audit passes faster. Example:

```latex
% Coordinate map:
% (A) at (0,0)  — 3cm x 1cm — "Start"
% (B) at (4,0)  — 3cm x 1cm — "End"
% Arrow: A -> B, label "Step 1" above
```

**Rule 4 — Use canonical templates for the three standard diagram types.** Rather than writing from scratch each time, start from these safe skeletons:

- *DAG (causal diagram):* nodes in a grid with `circle, minimum size=0.8cm`, arrows with `above` or `below` labels, bend angles never exceeding 30 degrees.
- *Flow chart:* nodes with explicit `minimum width=3.5cm, minimum height=1cm, text width=3cm, align=center`, vertical spacing of at least 1.5cm between node centers, labels always as standalone `\node` above arrow midpoints rather than inline edge labels.
- *RDD threshold diagram:* x-axis as a plain `\draw` line, threshold as a `\draw[dashed]` vertical, score dots as `\filldraw` circles with labels placed `above` or `below` with explicit `yshift`.

**Rule 5 — Never use `scale` on a complex diagram.** `scale` shrinks coordinates but not text, creating invisible collisions where the math looks fine but the rendered output is broken. If a diagram is too large, redesign the coordinate layout at the intended size.

**Rule 6 — Never define parameterized TikZ styles inside a Beamer frame.** In Beamer, `#` inside a frame body is consumed by the frame's argument parser before TikZ sees it, causing "Illegal parameter number" errors. These errors cascade through the entire compile and resist all downstream fixes (`##1`, `[fragile]`, `\catcode` hacks — none work reliably).

The fix: define ALL parameterized styles in the preamble using `\tikzset{}`:

```latex
% In the preamble — BEFORE \begin{document}:
\tikzset{
  mybox/.style={rectangle, draw=charcoal, thick, fill=lightbg,
                minimum width=3.5cm, minimum height=1cm,
                align=center, font=\small},
  myarrow/.style={->, thick, #1},
}
```

Inside frames, USE the styles but never DEFINE them with `#1`. This is not optional — it is a hard constraint of the Beamer/TikZ interaction. The workarounds (`##1`, `[fragile]`) are themselves fragile and create new failure modes.

---

## Step 5: The Compile Loop — ZERO TOLERANCE for Warnings

**Scott's standing rule: "I do not even tolerate cosmetic mistakes."** Overfull `\hbox`, underfull `\hbox`, overfull `\vbox`, underfull `\vbox`, font warnings, missing references — all of these must return zero counts before you hand the deck over, and they must also return zero counts at every *intermediate* checkpoint in this skill. A zero count on the final compile is not enough if intermediate compiles had warnings — the warnings must be actively eliminated as they appear, not left to accumulate.

### The compile check — run this verbatim after every edit

```bash
pdflatex -interaction=nonstopmode <deck>.tex
```

Then, **in this order**:

1. **Fatal errors.**
   ```bash
   grep "^!" <deck>.log
   ```
   Must return nothing. If anything, fix and recompile before moving on.

2. **Overfull / underfull box warnings.**
   ```bash
   grep -cE "Overfull|Underfull" <deck>.log
   ```
   **Must return exactly `0`.** Not "close to zero." Not "just a few small ones." Exactly zero. If the count is nonzero:
   - Run `grep -nE "Overfull|Underfull" <deck>.log` to see every instance with line numbers
   - For each warning, read the line number from the log (it tells you which line of the `.tex` file triggered it)
   - Apply the appropriate fix from the table below
   - Recompile
   - Re-run the count. Repeat until it is zero.

   | Warning type | Fix |
   |---|---|
   | `Overfull \hbox` | Rephrase shorter; use `\adjustbox{max width=\textwidth}`; add `@{}` to outer `tabular` columns; reduce font size on that line only; break a long URL with `\url{}` or `\nolinkurl{}` |
   | `Underfull \hbox` | Rephrase; adjust paragraph breaks; add `\hfill` or `\raggedright`; remove unnecessary line breaks |
   | `Overfull \vbox` | Split the slide; reduce `\vspace{}` values; shrink figure with `width=0.9\textwidth`; tighten list spacing; remove unnecessary `\vfill` |
   | `Underfull \vbox` | Add `\vfill` or `\vspace*{\fill}`; adjust `\topsep` / `\itemsep`; merge with another slide if truly underloaded |

   **Even 0.1pt overfull must be fixed.** LaTeX reports warnings for a reason — they indicate the compiler is making layout compromises you did not authorize. Letting "just one small one" through is the broken-windows failure mode.

3. **Font warnings.**
   ```bash
   grep -i "warning" <deck>.log | grep -i "font"
   ```
   Must return nothing. If any appear, it usually means a required font package is missing — install it and recompile.

4. **Missing references and labels.**
   ```bash
   grep -i "warning" <deck>.log | grep -iE "reference|label|citation"
   ```
   Must return nothing. Any `LaTeX Warning: Reference ... undefined` or `There were undefined references` must be resolved — either by defining the missing label, removing the reference, or running pdflatex a second time to pick up forward references.

5. **Open the PDF and visually inspect.**
   ```bash
   open <deck>.pdf
   ```
   Scroll through. Does every slide look clean? Are there any visual glitches you can't attribute to a specific warning? These are the silent failures — continue to Steps 6–8 to catch them.

### The circuit breaker — do not spiral

**If you have attempted 3 different approaches to fix the same compile error and it is not resolved, STOP.** Do not try a fourth approach. Do not keep editing and recompiling in a loop. Instead:

1. **Stop editing the .tex file.**
2. **Tell the user exactly what error you are seeing** — quote the log line.
3. **List the 3 approaches you tried and why each failed.**
4. **Ask the user how to proceed.**

The cost of stopping to ask is 2 minutes. The cost of spiraling is an hour of edits that make the file progressively worse. Every failed fix introduces new problems that obscure the original error. After 3 attempts, the file is harder to fix than it was before you started. The user can diagnose the root cause, suggest a different approach, or decide to simplify the slide.

**What counts as "the same error":** any error that persists at the same line (or moves to a nearby line) after your fix. "Illegal parameter number" that moves from line 568 to line 572 after your edit is the same error. An Overfull that appears on a different slide after you fixed the first one is a new error — reset the counter.

**This rule overrides "recompile until clean."** Zero tolerance for warnings is the goal, but zero tolerance does not mean infinite attempts. It means: fix what you can fix, and ask for help on what you cannot.

### The zero-tolerance rule applies at every checkpoint

This skill has multiple compile checkpoints:
- After Step 4 (first slide draft)
- After Step 6 (post `/tikz` cleanup)
- After Step 7 (post rhetoric audit fixes)
- After Step 8 (post graphics audit fixes)
- Step 9 (final compile)

**At each checkpoint, the full compile check above must pass with zero warnings before proceeding.** If you proceed to Step 7 with a lingering Overfull warning, you are not following the protocol. Fix it first.

### The final-compile gate

Before handing the deck to the user in Step 10, run the compile check one last time and confirm every counter is zero. If anything is nonzero, go back and fix it. Do not rationalize, do not explain it away, do not ship with known warnings.

---

## Step 6: Visual Cleanup — Invoke `/tikz`

LaTeX warnings catch box overflow. They do NOT catch:
- TikZ label collisions with arrows, boxes, or other labels
- ggplot2 / matplotlib labels clipped at figure boundaries
- Coordinate misalignment in custom diagrams
- Text bleeding into patches or shapes

Run `/tikz <deck>.tex` to audit every TikZ figure in the deck using the measurement-based collision-prevention protocol. The skill will:
- Compute Bézier curve depths and check for label overlaps
- Calculate text-width vs. node-gap for every edge label
- Verify boundary clearances for labels near shapes
- Check cross-slide consistency if the same diagram appears on multiple slides
- Report every collision with exact line numbers

Apply all fixes the skill suggests, then recompile. Go back to Step 5 if any new warnings appear.

---

## Step 7: Rhetoric Audit — Second Agent

Dispatch a sub-agent (via the Task tool) to evaluate the deck against the Rhetoric of Decks principles. Give it the following task prompt:

> You are Referee 2 in rhetoric-review mode. Audit the Beamer deck at `<deck>.tex` and its compiled PDF at `<deck>.pdf` against the principles in `~/.claude/skills/beautiful_deck/rhetoric_of_decks.md`. Check specifically:
>
> 1. **Titles are assertions.** Read the titles in sequence. Do they tell a coherent story? List any title that is a label rather than an assertion, with a suggested rewrite.
> 2. **Title line discipline.** Flag assertion titles that wrap or are likely to wrap. Suggest shorter one-line rewrites. Also flag avoidable word breaks or hyphenation used only to make text fit.
> 3. **One idea per slide.** List any slide with two or more competing ideas.
> 4. **No wall of sentences.** List any slide with more than two prose sentences stacked vertically.
> 5. **Microtext fit.** Check TikZ nodes, table cells, callout boxes, captions, and placeholders for ordinary words split across lines. Suggest wider boxes/columns, shorter phrases, local font changes, or layout changes.
> 6. **MB/MC equivalence.** Rate each slide's density on a 1–5 scale. Flag outliers (slides that are dramatically denser or sparser than their neighbors).
> 7. **Narrative arc.** Does the deck have a clear Setup / Development / Resolution structure? Does the opening hook and does the closing linger?
> 8. **Devil's Advocate.** Is there a slide addressing the strongest objection? If the context is academic or external, this is required.
> 9. **Audience fit.** Does the rhetorical balance (ethos / pathos / logos) match the audience declared at Step 0?
>
> Return a structured report with numbered concerns and suggested rewrites. Do NOT modify the deck source — only diagnose. The main agent will apply fixes.

When the sub-agent returns, apply every Major concern and as many Minor concerns as feasible, then go back to Step 5 and recompile.

---

## Step 8: Graphics Audit — Third Agent

Dispatch a second sub-agent focused ONLY on graphics. This is the step most people skip. Graphics errors don't trigger LaTeX warnings and they don't show up in rhetoric audits. They must be caught by explicit coordinate verification. Task prompt:

> You are a graphics auditor. Audit ONLY the figures, tables, and TikZ diagrams in the compiled PDF at `<deck>.pdf`. Do not evaluate rhetoric, narrative, or content. Check specifically:
>
> 1. **Numerical accuracy.** For every figure or table, verify that the numbers shown match the numbers in the underlying script output. Any mismatch is a critical error.
> 2. **Label positioning.** Are labels where they appear to be in the source code, or has the coordinate system drifted? For TikZ, verify intended coordinates match rendered positions. For ggplot2/matplotlib, verify axis labels, tick marks, legends, and annotations are not clipped or obscuring data.
> 3. **Axis and tick coherence.** Are axis ranges sensible? Are tick marks at meaningful intervals? Are tick labels readable?
> 4. **Color consistency.** Do figure colors match the deck palette? Are the same colors used consistently across figures for the same variables?
> 5. **Font sizing.** Are figure fonts readable at the back of the room (minimum 18pt equivalent in rendered form)?
> 6. **Table formatting.** Do tables use booktabs rules only? Are key coefficients highlighted? Is the decimal alignment consistent?
> 7. **Figure captions.** Does every figure have a caption that states what to conclude, not just what the figure is?
>
> Return a structured report with numbered concerns, each tied to a specific file path and line/coordinate. Do NOT modify any files — only diagnose.

Apply every fix, then recompile (Step 5) and re-run `/tikz` (Step 6). This is typically where the last round of silent errors get caught.

---

## Step 9: Final Compile

Run the compile loop one last time. Required state:

- Zero compile errors
- Zero Overfull warnings
- Zero Underfull warnings
- Zero font warnings
- `/tikz` audit returns no collisions
- Rhetoric audit sub-agent concerns all addressed
- Graphics audit sub-agent concerns all addressed
- The deck opens and displays correctly in a PDF viewer

If any of these are not true, go back to the relevant step. Do not hand the deck to the user in a state that isn't fully audited. Scott's rule: "I do not even tolerate cosmetic mistakes."

---

## Step 10: Deliver

Produce this directory structure:

```
<deck_name>/
├── <deck_name>.tex          # Main Beamer source
├── <deck_name>.pdf          # Compiled deck (clean)
├── <deck_name>_outline.md   # The Step 2 outline (keep for future iteration)
├── preamble.tex             # If the preamble is long enough to factor out
├── scripts/
│   ├── figure_1.R           # Standalone, runnable
│   ├── figure_2.R
│   ├── table_1.R
│   └── ...
├── figures/
│   ├── figure_1.pdf
│   ├── figure_2.pdf
│   └── ...
└── tables/
    ├── table_1.tex          # LaTeX fragment, \input-able
    └── ...
```

Report to the user:
- Path to the compiled PDF
- Slide count
- List of figures and tables generated
- List of accompanying scripts (for student walkthroughs)
- Summary of the rhetoric audit (what was flagged, what was fixed)
- Summary of the graphics audit (same)
- Any remaining TODOs or known limitations

---

## Reference: The Three Laws (per `rhetoric_of_decks.md`)

These are the constants that hold across every audience, every aesthetic, every deck. Read them once and internalize:

1. **Beauty is function.** Beauty in presentation is clarity made visible. Decoration without function is noise. The most beautiful slide may be three words on a blank background.
2. **Cognitive load is the enemy.** One idea per slide. Two max for inseparable contrasts. If you need "also" or "additionally," you need a new slide.
3. **The slide serves the spoken word.** The slide is the visual anchor for what you say — not what you say. If your slides can be understood without you speaking, you have written a document and called it a presentation.

## Reference: The Aristotelian triad (per `rhetoric_of_decks.md` Part II)

- **Ethos (credibility).** The audience asks: *Why should I trust this person?* Ethos lives in methodology slides, Devil's Advocate slides, honest scorecards, acknowledgment of limitations. Admitting weakness builds credibility.
- **Pathos (emotion).** The audience asks: *Why should I care?* Pathos lives in opening hooks, stakes, human impact, aspiration. Pathos without logos is demagoguery.
- **Logos (logic).** The audience asks: *Does this make sense?* Logos lives in data visualizations, comparison tables, causal diagrams, the logical flow from problem to conclusion. Logos without pathos is a lecture.

The rhetorical balance depends on the audience — see Q2 in Step 0.

---

## Full Philosophy Reference

For the complete essay behind these principles, all in this skill directory:
- `rhetoric_of_decks.md` — the condensed operational version
- `rhetoric_of_decks_full_essay.md` — the 600-line intellectual genealogy from Aristotle through LLMs
- `style_preferences.md` — user-specific stylistic defaults that persist across decks; separate from rhetorical principles.

This skill operationalizes those essays. You don't need to re-read them to execute the workflow — just follow the steps above.

## Local reference files

All in this skill directory (`~/.claude/skills/beautiful_deck/`):

- `preamble_warm_professional.tex` — Scott's house-style Beamer preamble (palette, fonts, footline, `\transitionslide` macro). Copy verbatim for Path A decks.
- `palette_reference.md` — alternative palettes with selection guidance for Path B (original-design) decks.
- `domain_patterns.md` — detailed structural patterns by audience (academic seminar, teaching lecture, working deck, etc.).
- `~/.claude/skills/tikz/tikz_rules.md` — measurement-based collision-prevention rules (lives in the `tikz` skill folder; this skill **depends on `/tikz` being installed**). READ before writing any TikZ figure (Step 4.4).

## Supporting skills

- `tikz` — the measurement-based visual collision audit. Invoked at Step 6.
- `referee2` — the full five-audit protocol. `beautiful_deck` uses its rhetoric-audit logic in Step 7.
- `split-pdf` — if the source content is a paper the user is reading, split it first and work from the summaries.
