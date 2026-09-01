# Blindspot (`/blindspot`)

> **Make the stone stony again. A peripheral vision audit that finds what the author cannot see — problems hiding in plain sight and opportunities being overlooked.**

---

## The idea

Viktor Shklovsky, the Soviet literary theorist, argued that art exists to restore perception. A man who walks barefoot up a mountain eventually cannot feel his feet. Everything becomes habitual, automatic, unconscious. Art exists to make the stone stony again — to force you to *feel* what you have stopped noticing.

Research has the same problem. By the time you've spent months on a paper, you can't feel the stones under your feet. The main finding has collapsed your attention. Everything else in the output — the spike at t=1, the missing subgroup, the heterogeneity richer than the average, the identification strategy stronger than you argued — has become invisible. Not because it's hidden, but because you stopped looking.

`/blindspot` makes the stone stony again.

---

## What it does

`/blindspot` audits your *perception* of your own output. It does not check whether your code is correct — that's `/referee2`. It checks whether you can see what's right in front of you.

The skill works through four quadrants — two **vices** (problems hiding in plain sight) and two **virtues** (opportunities being overlooked):

### The Blindspot Grid

|  | What's there but unseen | What's absent but unnoticed |
|---|---|---|
| **Problems** | Vice 1: The Unexplained Feature | Vice 2: The Convenient Absence |
| **Opportunities** | Virtue 1: The Unasked Question | Virtue 2: The Unexploited Strength |

### Vice 1: The Unexplained Feature

Something in the output that doesn't fit the story, but nobody asked about it. The t=1 spike. A coefficient that flips sign in one specification. A sample size that drops between columns without explanation.

The protocol: list every visible feature of the output before interpreting any of them. For each, ask what would generate this — starting with mundane explanations (rounding, sample restriction, measurement artifact) before substantive ones. Identify the single hardest feature to explain under the preferred interpretation.

### Vice 2: The Convenient Absence

Something that *should* be there but isn't. The dog that didn't bark. A robustness check never run. A subgroup never examined. A placebo test that doesn't exist. A pre-trend never plotted.

The protocol: ask what a hostile referee would demand to see. Which falsification tests are missing? Which subpopulations should have been checked? Where does N change without explanation?

### Virtue 1: The Unasked Question

A pattern in the output that suggests something more interesting than the finding being reported. Heterogeneity richer than the average effect. A mechanism visible in the data but absent from the hypothesis. A secondary finding hiding in the appendix.

The protocol: look at heterogeneity, mechanism evidence, secondary outcomes, and descriptive statistics. Is there a paper inside this paper that the author missed?

### Virtue 2: The Unexploited Strength

Something about the research design, data, or results that the author is underselling. Natural variation left on the table. A falsification test that would crush the main objection but was never run. An identification argument stronger than the paper claims.

The protocol: is the design stronger than argued? Is there a robustness check that would devastate the main criticism in one table? Are the descriptives undersold? Is the paper positioned too narrowly?

---

## How it differs from Referee 2

| | Blindspot | Referee 2 |
|---|---|---|
| **Question** | Can you see what's in front of you? | Is your code correct? |
| **Timing** | When output first appears, before writing | After the project is complete, in a fresh session |
| **Catches** | Overlooked problems (vices) and overlooked opportunities (virtues) | Coding errors, replication failures, bad controls |
| **Would have caught the t=1 spike?** | Yes | No |
| **Would have caught a merge error?** | Maybe | Yes |

They are complements, not substitutes. Run `/blindspot` first (on fresh output, before interpretation), then `/referee2` later (on the completed project, in a separate session).

---

## Usage

```
/blindspot path/to/figure_or_table "brief description of what you think the main finding is"
```

The skill produces a **Blindspot Report** with findings organized by quadrant, each marked DONE or FLAG, and a ruling:

- **CLEAR** — proceed to interpretation. No vices found; virtues noted.
- **CONDITIONAL** — proceed but acknowledge open questions. Vices flagged but manageable.
- **HOLD** — do not interpret or publish until flagged vices are resolved.

---

## Origin and inspiration

This skill was inspired by conversations with Jason Fletcher (University of Wisconsin), who commented on Scott Cunningham's Substack post (Claude Code 35, March 2026) and asked about the spikes at t=1 and t=3 in a figure where Scott had focused entirely on the spike at t=2. The spike at t=1 was the tell — it was inconsistent with the p-hacking interpretation and pointed immediately to rounding. Fletcher described this habit as something passed down from his own graduate training. He wrote about it in ["Owning All the Numbers"](https://jasonmfletcher.substack.com/p/owning-all-the-numbers).

The theoretical frame comes from Viktor Shklovsky's "Art as Device" (1917): the purpose of art is to restore perception, to make the stone stony again.

## Related skills

- **`/referee2`** — the correctness audit. Blindspot checks perception; Referee 2 checks implementation. Run both.
- **`/beautiful_deck`** — invokes a rhetoric audit sub-agent during deck creation. Blindspot is for empirical output, not slides.
