# Protocol S — Split-PDF Pipeline

*Input:* absolute path to the PDF, absolute path to the splits directory (`references/raw/raw_build/split_<basename>/`). The main session has already run the splitter — the splits directory is populated with `<basename>_pp<X>-<Y>.pdf` chunks before this subagent is spawned. Do not attempt to split the PDF yourself.

## Step 1: Read splits in batches of 3

Read each split sequentially in batches of 3, without pausing or asking for confirmation. After each batch, append findings to `<splits-dir>/notes.md` under the structured-extraction dimensions in `common.md`, preceded by a batch boundary comment:

```
<!-- batch N: pp X-Y -->
```

If `notes.md` already exists (prior interrupted run), read it first and resume from where it left off — do not overwrite earlier content. `notes.md` is append-mostly and permanent; never delete it.

## Step 2: Synthesize `_text.md`

After all splits are read, write `references/raw/<basename>_text.md` from the accumulated `notes.md` content. Follow the `_text.md` structure in `common.md` (bib block, plain-English synthesis, 12 dimensions).

For the bib metadata block: scan the first split for the DOI regex `10\.\d{4,}/\S+`. Extract authors, title, year, and venue from the first-split text. Record null for any field not found.

`notes.md` is permanent — do not delete it after writing `_text.md`.

## Step 3: Write wiki pages

Use the substantive-change rule and relevance filtering in `common.md`.

For figures: Protocol S does not have extracted figure images. Use CLIP placeholders for all Tier B figures and for any Tier A data figures that cannot be adequately described in text. A structured Tier A block suffices when the data description is complete; use a CLIP placeholder when it isn't.

CLIP placeholder format in `_text.md`:

```
> **Figure N (CLIP):** <verbatim caption> (p. 12)
> One-liner: <what the figure depicts at a glance>
> ACTION: clip from PDF, save to references/wiki/figures/<basename>_fig<N>.png
```

When a wiki page references a CLIP figure, use a broken image link (it renders as a visible TODO):

```markdown
![<short description>](figures/<basename>_figN.png)
*<verbatim caption> ([<basename>](../log.md), p. 12)*
```

All wiki pages live directly under `references/wiki/`. For Protocol S CLIP placeholders, use `figures/<basename>_figN.png` in wiki markdown, never `../figures/...`.

Before writing any CLIP placeholder that references the figures directory, ensure it exists: `mkdir -p references/wiki/figures`.

## Return value additions for Protocol S

```
Pending CLIPs: [list of {target_path, source_paper, page_number, one_liner}]
```
