# `/read-pdf` — Canonical Academic PDF Reader

**Skill location:** [`.claude/skills/read-pdf/SKILL.md`](../../.claude/skills/read-pdf/SKILL.md)

`/read-pdf` reads academic papers and writes reusable `<basename>_text.md` notes with bibliographic metadata plus 8 research dimensions.

## Modes

| Mode | Command | Best for |
|---|---|---|
| Marker conversion | `/read-pdf <paper>` | Tables, equations, figures, repeated processing, batch ingest |
| Split vision reading | `/read-pdf --split <paper>` | Triage, converter failures, no marker setup, legacy `/split-pdf` behavior |

Default mode converts the PDF to markdown locally with marker, using:

```bash
python3 ~/.claude/skills/read-pdf/install.py
python3 ~/.claude/skills/read-pdf/convert.py path/to/paper.pdf
```

Split mode creates 4-page chunks with:

```bash
python3 ~/.claude/skills/read-pdf/scripts/split.py path/to/paper.pdf
```

`/split-pdf` remains as a compatibility wrapper for `/read-pdf --split`.

## Output

Both modes preserve the original PDF and write:

```text
paper.pdf
paper_text.md
```

Split mode also writes working files under:

```text
<foldername>_build/split_<basename>/
```

The structured extraction contract lives in [`.claude/skills/read-pdf/extraction_schema.md`](../../.claude/skills/read-pdf/extraction_schema.md).

## Isolation

When another skill calls `/read-pdf`, heavy reading runs in a subagent:

- marker mode: [`.claude/skills/read-pdf/isolation_read.md`](../../.claude/skills/read-pdf/isolation_read.md)
- split mode: [`.claude/skills/read-pdf/isolation_split.md`](../../.claude/skills/read-pdf/isolation_split.md)
