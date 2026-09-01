# Alternative Output Formats

Loaded only when the user explicitly requests a non-Beamer format in Q5. Beamer is the default and covered inline in `SKILL.md`.

## Accepted alternatives (on explicit user request only)

- **Quarto (`.qmd` → HTML / reveal.js or PDF / Beamer)** — accepted if the user says "Quarto" or "reveal.js". Produces HTML slides with live code execution; good for live coding demos.
- **R Markdown (`.Rmd` → xaringan or ioslides)** — accepted if the user specifies. Mostly superseded by Quarto.
- **Typst** — accepted if the user specifies. Newer, faster compiles, less mature ecosystem.
- **Raw HTML / reveal.js** — accepted if the user specifies. Full web control, needs a browser to present.
- **Pure markdown → Marp** — accepted if the user specifies. Lightweight, limited typographic control.

## What stays the same regardless of format

The Three Laws and the Aristotelian balance are unchanged. The format is the medium; the rhetoric is the substance. Everything in `SKILL.md` applies — one idea per slide, assertion titles, MB/MC equivalence, code-first figure generation, the rhetoric and graphics audits. Only the specific compile commands and preamble syntax change.

You still produce the same outline (Step 2), the same code-first scripts (Step 3), the same rhetoric audit (Step 7), and the same graphics audit (Step 8). The preamble becomes a Quarto YAML header, a Typst style block, or a reveal.js CSS file instead of a Beamer `.sty`, but the design principles from Step 1 still apply.

## Theme requirement still applies

- **Quarto / reveal.js:** custom CSS, custom theme file, overridden defaults. Do not ship the default Quarto theme.
- **Typst:** custom style block with real design choices, not the default.

Under no circumstances ship boilerplate.
