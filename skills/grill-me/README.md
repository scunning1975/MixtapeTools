# Grill Me (`/grill-me`)

> **A relentless interview about your plan or design — one question at a time, walking down the decision tree.**

`/grill-me` interviews you about whatever plan, design, or proposal you're working on, asking one focused question at a time, providing its recommended answer for each, and continuing until every branch of the decision tree has been resolved.

## What it does

When you invoke `/grill-me [optional context]`, Claude takes the position of a thoughtful collaborator who refuses to let you skip past unresolved decisions. It walks down the design tree, surfacing dependencies between choices and forcing each one to be made explicitly before moving on.

For each question:
- The question is asked one at a time
- Claude provides its recommended answer with reasoning
- If the question can be answered by reading the codebase, Claude reads the codebase instead of asking you
- The conversation continues until shared understanding is reached

## When to use it

- Before implementing something nontrivial
- When a plan feels vague
- When you want a stress test
- For open-ended audits of a directory, skill, paper, or artifact

## Usage

```
/grill-me
/grill-me [the plan / design / topic]
/grill-me audit my custom skills before sharing with colleagues
/grill-me whether this identification strategy holds up
```

## Acknowledgments

The `SKILL.md` is taken verbatim from [Matt Pocock's grill-me skill](https://github.com/mattpocock/skills/tree/main/skills/productivity/grill-me). Full credit for the skill's behavior and design goes to him. The contribution here is packaging and documentation for this skills collection.
