# Isolation: Split Mode

The parent acquires the PDF, resolves existing extract/split reuse, and runs `scripts/split.py` if needed. The parent then launches a subagent for split-PDF reading and extraction.

```text
Read PDF split files and produce structured extraction notes.

Split directory: <split_dir>
Files, in order: <file_list>
Notes output:    <notes_path>
Text output:     <text_path>
Schema:          ~/.claude/skills/read-pdf/extraction_schema.md

Process:
1. Read 3 PDF files at a time using the Read tool.
2. After each batch, update <notes_path> with extracted content.
3. Extract the bibliographic metadata block and 12 research dimensions as specified in extraction_schema.md.
4. Write the final structured extraction to <text_path>, with the ## Bibliographic metadata block first.

Report when done: splits read, figures/tables found, one-sentence content summary.
```

After the subagent returns, the parent reads `_text.md` only.
