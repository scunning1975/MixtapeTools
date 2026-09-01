# Isolation Common

When `/read-pdf` is invoked by another skill or workflow, heavy reading runs in a subagent. The parent may run lightweight shell steps, choose the mode, check cache/extract collisions, and read the final `_text.md`. The parent must not read bulky intermediate inputs (`markdown.md` or split PDF images) directly.

Use:

- `isolation_read.md` for default marker mode.
- `isolation_split.md` for `--split` mode.

Standalone invocations may read in the main conversation because there is no larger workflow context to protect.
