# Protocol E — Cached Extract

*Input:* path to `references/raw/<basename>_text.md`.

## Step 1: Read the extract

Read `_text.md` in full. Extract the `## Bibliographic metadata` block for the return value. Note any CLIP placeholders in the figures sections.

Protocol E reads only the cached `_text.md` and any figure files it references. Do not re-read the PDF with `pdftotext` to expand or validate the extract.

## Step 2: Write wiki pages

Use the substantive-change rule and relevance filtering in `common.md`.

For figures: if `_text.md` references wiki figure paths that already exist on disk, embed them in wiki pages using the same lightweight format as Protocol M. If `_text.md` contains CLIP placeholders, pass them through to the wiki and aggregate them into the Pending CLIPs return field.

Do **not** re-synthesize or overwrite `_text.md` — it is the canonical extract for this paper.

## Return value additions for Protocol E

```
Pending CLIPs: [list of {target_path, source_paper, page_number, one_liner} — forwarded from _text.md]
```
