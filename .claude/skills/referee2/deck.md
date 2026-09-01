## Mode 1: Deck Review

### What to Read First
1. `~/.claude/skills/referee2/referee2.md` (your persona)
2. `~/.claude/skills/beautiful_deck/rhetoric_of_decks.md` (the standard)
3. `~/.claude/skills/tikz/tikz_rules.md` (TikZ collision prevention — margin rules, curve clearance, Bézier calculations)
4. The project's `CLAUDE.md` if one exists (project-specific slide rules)
5. The `.tex` file being reviewed

### The Deck Audit Checklist

For EVERY slide, assess:

1. **One idea per slide** (two max for inseparable contrasts)
   - State the slide title
   - State the one idea
   - Flag violations

2. **No wall of sentences** (HARD RULE)
   - No prose sentences on slides
   - Text must be: labeled setups, single concluding lines, or structured content
   - Check every `\deemph{}`, every `\textcolor{}` block

3. **Titles are assertions, not labels**
   - "Results" is bad. "Treatment increased turnout by 5pp" is good.

4. **TikZ coordinate verification and margin spacing**
   - Check that axis labels align with data positions
   - Check that labels don't overlap or clip
   - Check that coordinates are mathematically consistent
   - **Margin rule**: Every pair of visual objects (labels, arrows, axes, boxes) must have visible margin space between them. No two objects should touch or visually collide. Minimum clearances: label↔label 0.3cm, label↔axis 0.3cm, label↔arrow 0.3cm, any object↔slide edge 0.5cm. See `~/.claude/skills/tikz/tikz_rules.md` Pass 5 for the full table.
   - **Plotted curve clearance**: For any `\draw plot` with a mathematical function (especially normal curves), **compute the curve's y-value** at every x-coordinate where another object exists. Verify ≥0.3cm clearance. Never eyeball where a curve passes — calculate it from the equation. See `~/.claude/skills/tikz/tikz_rules.md` Pass 5b.

5. **Compile cleanliness**
   - Compile with `pdflatex -interaction=nonstopmode`
   - **After compiling, read the `.log` file directly** (do NOT rely only on grepping terminal output — grep produces false positives from package description strings and can miss real warnings)
   - In the log, search for these exact LaTeX warning patterns:
     - `Overfull \\hbox` or `Overfull \\vbox`
     - `Underfull \\hbox` or `Underfull \\vbox`
     - Lines starting with `!` (LaTeX errors)
     - `LaTeX Warning:` (label, reference, font warnings)
   - Ignore lines that merely contain the word "warning" inside package metadata (e.g., `infwarerr` package descriptions)
   - Zero overfull hbox. Zero overfull vbox. Zero underfull warnings. Zero errors.
   - If warnings exist, report them with exact line numbers from the log.

6. **Narrative flow**
   - Does it open with a concrete application, not an abstract claim?
   - Does it build intuition before notation?
   - Does the arc make sense?

7. **Problem set alignment** (if applicable)
   - Does the deck prepare students for the current problem set?
   - Are the tools and notation consistent?

### Output
File your report at `correspondence/referee2/` (or as specified by the user). If that directory does not exist yet in the project, create it lazily before writing — `mkdir -p correspondence/referee2`. Include:
- Slide-by-slide audit table
- Specific issues with line numbers
- Verdict: Accept / Minor Revision / Major Revision
- Prioritized recommendations

---
