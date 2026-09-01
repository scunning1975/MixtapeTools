# Per-citation mode

One Agent subagent per `.bib` entry. Each fully audits its single entry against canonical sources, then a final reviewer consolidates.

## Step 3a.1 — Launch agents in waves of `--max-parallel`

For each `entries/*.bib` file, dispatch one Agent subagent (subagent_type: general-purpose) with this brief:

```
You are auditing one bibliography entry. The entry is:

<paste the .bib block>

Your job:
1. Identify the cited paper. Use WebSearch (and WebFetch if needed) to find it.
2. Locate a canonical anchor: DOI, journal landing page URL, or author working-paper URL.
3. Cross-check every field in the .bib block against the canonical source:
   - title, authors, year, journal/booktitle, volume, number, pages, publisher, DOI
4. Specifically test for "field mixing" — e.g., the title belongs to one paper but the authors or year belong to another. This is the most common silent error in inherited .bib files.
5. Output JSON to <reports/<key>.json> with:
   - status: "clean" | "corrected" | "unverifiable"
   - one_sentence: plain-language description of the paper (one sentence)
   - canonical_url: DOI or URL
   - issues: list of {field, original, corrected, reason}
   - corrected_bib: the corrected entry (or the original if status=clean)

You do NOT modify the input file. You only write the report and the corrected entry.
```

## Step 3a.2 — Final reviewer pass

When all entries are done, dispatch a single reviewer agent that:

- Reads every `reports/*.json`.
- Spot-checks any entry marked "unverifiable" (does a quick second WebSearch).
- Adjudicates conflicts where a corrected field looks suspicious.
- Writes `bibcheck_report.md` with a summary table (Clean / Corrected / Unverifiable counts) and per-entry detail.
- Concatenates the corrected_bib fields into `corrected.bib`.
