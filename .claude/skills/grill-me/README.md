# Grill Me (`/grill-me`)

> **A relentless interview about your plan or design — one question at a time, walking down the decision tree.**

`/grill-me` is the simplest skill in the kit. It does one thing: it interviews you about whatever plan, design, or proposal you're working on, asking one focused question at a time, providing its recommended answer for each, and continuing until every branch of the decision tree has been resolved.

## What it does

When you invoke `/grill-me [optional context]`, Claude takes the position of a thoughtful collaborator who refuses to let you skip past unresolved decisions. It walks down the design tree, surfacing dependencies between choices and forcing each one to be made explicitly before moving on.

For each question:
- The question is asked one at a time (never a list — each answer changes what comes next)
- Claude provides its **recommended answer** with reasoning, so you can agree, disagree, or redirect
- If the question can be answered by reading the codebase, Claude reads the codebase instead of asking you
- The conversation continues until shared understanding is reached

## When to use it

- **Before implementing** something nontrivial — when there are too many open design questions to start writing code yet
- **When a plan feels vague** — invoke `/grill-me` to surface the decisions you've been glossing over
- **When you want a stress test** — to check whether your design holds up under interrogation
- **For audits** — pointing it at a directory, a skill, a paper, or any artifact and asking for a structured review

## Usage

```
/grill-me                              # generic — Claude asks what to grill you about
/grill-me [the plan / design / topic]  # interrogation begins immediately
/grill-me audit my custom skills before sharing with colleagues
/grill-me whether this identification strategy holds up
```

The argument is free-form — describe what you want grilled, and Claude will treat it as the subject of the interview.

## Philosophy

The skill exists because most plans fail at points the author already noticed but didn't want to think about. A relentless interviewer who walks the decision tree and refuses to skip ahead surfaces those points before they become bugs, lost work, or wasted code.

The "one question at a time" rule is structural, not stylistic. A list of questions invites batch answers; batch answers invite hand-waving. A single question, with a single recommended answer, demands a single explicit decision.

## Files in this skill

- [`SKILL.md`](SKILL.md) — the skill definition. Very short. The skill's behavior is the protocol, not a long instruction set.

## Related skills

- **`/blindspot`** — also an interrogation tool, but pointed at empirical *output* (figures, tables) rather than plans. `/grill-me` walks the design tree before work starts; `/blindspot` walks the perception tree after results exist.
- **`/referee2`** — a structured implementation audit. `/grill-me` is open-ended; `/referee2` runs a fixed five-audit checklist.

## Acknowledgments

The `SKILL.md` is taken verbatim from [Matt Pocock's grill-me skill](https://github.com/mattpocock/skills/tree/main/skills/productivity/grill-me) — full credit for the skill's behavior and design goes to him. The only contribution here is this README, which adds a human-readable explanation of what the skill does, when to use it, and how it relates to the other skills in this collection.
