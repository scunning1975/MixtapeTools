# `/read-pdf` — Download, Convert, Split, and Deep-Read Academic Papers

`/read-pdf` is the canonical academic-paper reading skill. By default, it uses python:marker to convert the PDF to markdown locally before extracting structured notes. With `--split`, it uses a split-PDF vision-batch path.

**Skill location:** [`.claude/skills/read-pdf/SKILL.md`](../../.claude/skills/read-pdf/SKILL.md)

---

## What This Skill Does

You give Claude a paper — either a local PDF file or a search query — and it does the rest. It finds and downloads the paper (or uses your local file in place), reads it through the selected backend, and writes a persistent `_text.md` extraction alongside the source PDF.

Both modes produce the same output contract: bibliographic metadata, plain-English synthesis, and 12-dimension research notes.

| Mode | Command | Best for |
|---|---|---|
| Marker conversion | `/read-pdf <paper>` | Tables, equations, figures, repeated processing, batch ingest |
| Split vision reading | `/read-pdf --split <paper>` | Triage, converter failures, no marker setup |

---

## Mode Choice

Default mode converts the PDF to layout-aware markdown before extraction. Use it for normal paper ingest, tables, equations, figures, repeated processing, and batch wiki updates.

Use `--split` when marker setup is unavailable, marker cannot parse a malformed PDF, or first-split triage is enough. Split mode has two limitations:

1. **Equation fidelity.** PDF page images render math as bitmaps. Vision-reading bitmaps can produce approximate LaTeX transcriptions.

2. **Table structure.** Complex tables (multi-column headers, merged cells, footnotes) are harder to transcribe accurately from images than from a layout-aware text conversion.

---

## Default Mode

Convert the PDF to markdown with python:marker (layout-aware, GPU-accelerated), build bounded chunks, then extract through worker notes and one neutral synthesis pass.

### How It Works

| Step | Action |
|------|--------|
| **Acquire** | Download the PDF (via web search) or use a local file in place |
| **Install** | `install.py` sets up the marker venv on first run (~500 MB, one-time), then reuses it; monthly advisory check for marker major updates |
| **Check cache** | SHA-256 hash check — skip re-conversion if markdown already cached |
| **Convert** | `convert.py` runs marker and writes `markdown.md` to a content-hash cache |
| **Collision** | If `_text.md` already exists, ask: overwrite or save as `_text2.md`? |
| **Check extract cache** | If `text.md` exists in the converter cache, copy it beside the PDF and skip extraction |
| **Prepare substrate** | Split cached `markdown.md` into bounded chunk files plus `manifest.json` |
| **Extract** | Workers read assigned chunks; synthesis reads worker notes and writes bibliographic metadata, plain-English synthesis, and 12-dimension notes |
| **Persist** | Save final extraction to `<basename>_text.md` alongside the source PDF and to `text.md` in the converter cache |

### Usage

```
/read-pdf path/to/paper.pdf
/read-pdf "Gentzkow Shapiro Sinkinson 2014 competition newspapers"
/read-pdf --split path/to/paper.pdf
```

You must tell Claude what paper to read. Provide either a local file path or a search query specific enough to find the paper.

---

## Split Mode

`/read-pdf --split` uses this directory convention:

```text
articles/
├── smith_2024.pdf
├── smith_2024_text.md
└── articles_build/
    └── split_smith_2024/
        ├── smith_2024_pp1-4.pdf
        ├── smith_2024_pp5-8.pdf
        ├── smith_2024_pp9-12.pdf
        └── notes.md
```

The splitter script is:

```bash
python3 ~/.claude/skills/read-pdf/scripts/split.py path/to/paper.pdf
```

### What Gets Extracted

Both modes extract the same 12 dimensions, plus a bibliographic metadata block and plain-English synthesis at the top of `_text.md`:

```
## Bibliographic metadata
doi: <10.xxxx/yyyy or null>
authors: [LastName1, LastName2, ...]
title: <verbatim title>
year: <year>
venue: <journal/working paper series/etc.>
venue_type: journal | working_paper | book_chapter | other
```

1. **Research question** — What is the paper asking and why does it matter?
2. **Audience** — Which sub-community of researchers cares about this?
3. **Method** — How do they answer the question? What is the identification strategy?
4. **Target parameter** — What estimand or causal/statistical object is targeted?
5. **Data** — What data do they use? Where did they find it? Unit of observation? Sample size? Time period?
6. **Statistical methods** — What econometric or statistical techniques? Key specifications?
7. **Findings** — Main results? Key coefficient estimates and standard errors?
8. **Contributions** — What is learned that we didn't know before?
9. **Replication feasibility** — Public data? Replication archive? Data appendix? URLs?
10. **Tables** — Inventory tables; extract machine-readable tables when central.
11. **Figures** — Inventory figures, captions, and key visual claims.
12. **Equations / formal objects** — Inventory equations, model primitives, algorithms, propositions, and labeled specifications.

---

## Key Features

### Conversion backend: marker

The conversion backend is **marker** (`marker-pdf`). Selected after a head-to-head bake-off against docling on a representative set of empirical-economics PDFs; marker won on equation fidelity, table structure, and figure extraction quality.

Backend selection is fixed in `convert.py`. There is no runtime override — if the bake-off needs to be redone for a future backend candidate, edit the `BACKEND` constant in `convert.py` explicitly so the cache namespace and venv are regenerated cleanly.

`install.py` installs the current PyPI `marker-pdf` release only when the marker venv is first created. If marker already imports cleanly, setup reuses it and performs at most one lightweight PyPI check every 30 days. It warns only when PyPI has crossed a marker major-version boundary, and it never auto-upgrades.

If the user opts into a major upgrade, run:

```bash
python3 ~/.claude/skills/read-pdf/install.py --upgrade-marker
```

Existing cached conversions remain in place. To force fresh conversions after upgrading, delete selected cache entries under `~/.cache/claude-pdf-converter/cache/marker/`, or delete that whole directory. Rebuilding a large cache can be very time-consuming.

### Born-digital PDFs and OCR

Most journal PDFs already contain an embedded text layer. For those files, `convert.py` samples the first pages with `pdftotext` and tells marker to use the embedded text rather than re-OCRing the whole document. Marker still performs layout, table, and selected region recognition, but avoids the extremely slow full-document OCR path. If the text-layer sample is missing or too sparse, marker keeps OCR enabled for scanned PDFs.

### GPU acceleration

Auto-detected: NVIDIA CUDA → CPU. MPS on Apple Silicon is excluded — surya's layout model crashes at runtime on MPS with an index-bounds error (some surya sub-models already refuse MPS; the layout model does not and fails mid-conversion). A 3–5× speedup on CUDA boxes. No flags needed on any platform.

### Content-hash cache

Conversions are cached by SHA-256 of the source PDF bytes at `~/.cache/claude-pdf-converter/cache/marker/<hash>/`. Re-converting the same PDF (even under a different filename, even in a different project) is a no-op — the cached `markdown.md` is returned immediately. The cache is shared across all projects on the machine.

Cache entries are not auto-evicted. To force a re-conversion:
```bash
rm -rf ~/.cache/claude-pdf-converter/cache/marker/<hash>/
```
To wipe the entire cache (e.g., after a marker upgrade, if you explicitly want all conversions rerun):
```bash
rm -rf ~/.cache/claude-pdf-converter/cache/
```
The venv at `~/.cache/claude-pdf-converter/venv-marker/` is untouched.

### `_text.md` collision handling

If a `_text.md` already exists alongside the PDF, default mode asks whether to overwrite it or save the new extraction as `_text2.md`. Split mode asks whether to reuse the existing extract or re-read from scratch.

### Agent isolation protocol

When another skill calls `/read-pdf`, heavy reading runs inside a subagent. The mode-specific protocols live in:

- `isolation_read.md` for marker mode.
- `isolation_split.md` for `--split` mode.

---

## Mode Tradeoffs

| | `--split` | default marker mode |
|---|---|---|
| **Reading mechanism** | Claude vision-reads PDF page images | Marker converts to markdown; Claude reads text |
| **Setup required** | None | `install.py` (~500 MB, one-time) |
| **First-run latency** | None | ~1–3 min (model download + conversion) |
| **Subsequent runs** | — | Instant if cached |
| **Equation fidelity** | Good (vision-based) | Better (native LaTeX extraction) |
| **Table structure** | Good | Better (layout-aware) |
| **Works without internet** | No (unless PDF already local) | Yes (after install) |
| **Output format** | `_text.md` | `_text.md` (same format) |

Both modes produce identical `_text.md` output format and can be used interchangeably by downstream skills like `/bib-update` and `/wiki-update`.

---

## Limitations

- **Requires local setup.** First run downloads ~500 MB of models. Not suitable for environments where you can't write to `~/.cache/`.
- **Conversion can fail on malformed PDFs.** If `convert.py` errors, the default mode stops — it does not fall back silently. Use `--split` if you want the vision-batch fallback.
- **Default mode is not ideal for triage.** If you just need to decide whether a paper is relevant, use `--split` and read the first split.

---

## Origin

This skill is maintained in [Scott Cunningham](https://github.com/scunning1975/MixtapeTools)'s MixtapeTools repository.
