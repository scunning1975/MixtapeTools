# Step 1 Path B — Designing an Original Theme

Loaded only when the user picks Path B in Q3 (the default when Scott says "design for me an original Beamer style"). Path A (Scott's house style) is a one-line action in `SKILL.md`: copy `preamble_warm_professional.tex`.

Before implementing, read `~/.claude/skills/beautiful_deck/style_preferences.md`. Treat it as user-specific stylistic guidance only: it shapes persistent visual preferences such as slide-header treatments, but does not override audience fit, content needs, or the rhetorical principles in `rhetoric_of_decks.md`.

## 1.1 Palette construction

Pick a core accent (one color, not an ensemble). This is the emotional anchor of the deck. The examples below illustrate audience-to-color reasoning; they are not a house palette to reuse by default.

| Audience | Core accent | Why |
|---|---|---|
| Undergraduate data science | Teal #048A81 | Fresh, energetic, reads as "modern" without being juvenile |
| PhD causal inference seminar | DeepNavy #2E4057 | Serious, anchored, matches the rhetorical weight of identification |
| Policy / applied work | WarmOrange #E85D04 | Human warmth, urgency, signals "this matters" |
| Conference theory talk | SoftPurple #9D4EDD | Distinctive, academic, unusual enough to be remembered |

Around the core, build a 10-color palette: 1 core accent, 1 secondary accent (analogous or complementary), 2 neutrals for text (one dark, one warm gray), 2 background neutrals (cream + white), 1 alert color (usually a deep red), 1 success / positive color (usually forest green or teal), 2 tertiary colors for charts. Define them all in `\definecolor{}` at the top of the preamble.

Use https://www.viget.com/articles/color-contrast/ as a WCAG-AA reference — all body text must have contrast ratio ≥ 4.5:1 against background.

## 1.2 Frame-title style

Pick ONE visual treatment for frame titles. Options that read well:
- **Left rule:** a thin colored vertical bar to the left of the title (2mm wide, core accent color)
- **Underline:** a 1pt horizontal rule below the title in core accent
- **Background tint:** a very light tint of the core accent behind the title area
- **Simple bold:** no decoration, just bold dark text with generous white space

Do NOT combine multiple. Pick one and use it consistently.

## 1.3 Bullet style

If bullets appear at all, use a single `\tikz\fill` circle in the core accent, sized to match the text baseline. Subitems get a smaller circle in the secondary accent. No standard Beamer triangles, no arrows, no squares.

## 1.4 Section dividers

Full-bleed dark background (core accent or a dark neutral), white text, one large label centered. Use `\transitionslide{Title}{Subtitle}` pattern defined in `preamble_warm_professional.tex`. This creates the "deck breathes" rhythm — a moment of rest between sections.

## 1.5 Typography

- `\usefonttheme{professionalfonts}` — required.
- Body text: 24pt minimum. Title: `\huge`. Frame title: `\Large\bfseries`. Footnote floor: 18pt.
- Sans-serif. If you want a custom font, use one already installed: `lmodern` (default), `roboto`, `fira`, or `utopia`. Do NOT require the user to install fonts.
- Never justify text. Always ragged right (`\RaggedRight`).

## 1.6 Write the preamble

Output the full preamble to `<deck_name>.tex`. Include every package needed, every color, every beamer color assignment, every font setup, and the `\transitionslide` macro. The preamble is boring but load-bearing — get it right on the first pass so you don't have to revisit.
