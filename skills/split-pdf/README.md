# `/split-pdf` — Compatibility Wrapper

**Skill location:** [`.claude/skills/split-pdf/SKILL.md`](../../.claude/skills/split-pdf/SKILL.md)

`/split-pdf` is retained for existing slash-command muscle memory. Treat it as:

```text
/read-pdf --split <same arguments>
```

The canonical split workflow now lives in [`.claude/skills/read-pdf/SKILL.md`](../../.claude/skills/read-pdf/SKILL.md), under `--split` mode.

## What Still Works

- Original PDF is preserved.
- Split files are written under `<foldername>_build/split_<basename>/`.
- Working notes are accumulated as `notes.md`.
- Final reusable extraction is saved as `<basename>_text.md`.
- Old script path `~/.claude/skills/split-pdf/scripts/split.py` remains as a shim to the canonical `~/.claude/skills/read-pdf/scripts/split.py`.

For batching rationale, see [`.claude/skills/split-pdf/methodology.md`](../../.claude/skills/split-pdf/methodology.md).
