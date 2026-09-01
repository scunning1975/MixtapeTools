# `/read-pdf` — Download, Convert, and Deep-Read Academic Papers

**Same workflow as `/split-pdf`, but uses python:marker to convert the PDF to markdown locally first, instead of having Claude vision-read PDF page images.** This makes equation, table, and figure extraction more faithful, and avoids image-based context bloat in the parent conversation.

**Skill location:** [`.claude/skills/read-pdf/SKILL.md`](../../.claude/skills/read-pdf/SKILL.md)

---

## What This Skill Does

You give Claude a paper — either a local PDF file or a search query — and it does the rest. It finds and downloads the paper (or uses your local file in place), converts it to clean markdown using python:marker, then reads that markdown to write structured notes. When finished, it saves a persistent `_text.md` extraction alongside the source PDF, in the same format produced by `/split-pdf`.

---

## Why It Exists

`/split-pdf` reads PDFs by having Claude vision-read page images in batches. This works well for most papers but has two limitations:

1. **Equation fidelity.** PDF page images render math as bitmaps. Vision-reading bitmaps produces approximate LaTeX transcriptions. Papers heavy with structural equations (e.g., structural IO, dynamic programming models) benefit from native math extraction.

2. **Table structure.** Complex tables (multi-column headers, merged cells, footnotes) are harder to transcribe accurately from images than from a layout-aware text conversion.

`/read-pdf` addresses both by running a local conversion step first. The result is a `markdown.md` file where equations are native LaTeX math mode and tables are pipe-syntax markdown — readable as text rather than image bitmaps.

---

## The Solution

Convert the PDF to markdown with python:marker (layout-aware, GPU-accelerated), then read the text.

### How It Works

| Step | Action |
|------|--------|
| **Acquire** | Download the PDF (via web search) or use a local file in place |
| **Install** | `install.py` sets up the marker venv on first run (~500 MB, one-time) |
| **Check cache** | SHA-256 hash check — skip re-conversion if markdown already cached |
| **Convert** | `convert.py` runs marker and writes `markdown.md` to a content-hash cache |
| **Collision** | If `_text.md` already exists, ask: overwrite or save as `_text2.md`? |
| **Extract** | Read `markdown.md`, write bibliographic metadata + 8-dimension notes |
| **Persist** | Save final extraction to `<basename>_text.md` alongside the source PDF |

### Usage

```
/read-pdf path/to/paper.pdf
/read-pdf "Gentzkow Shapiro Sinkinson 2014 competition newspapers"
```

As with `/split-pdf`, you must tell Claude what paper to read. Provide either a local file path or a search query specific enough to find the paper.

### What Gets Extracted

Same 8 dimensions as `/split-pdf`, plus a bibliographic metadata block at the top of `_text.md`:

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
4. **Data** — What data do they use? Where did they find it? Unit of observation? Sample size? Time period?
5. **Statistical methods** — What econometric or statistical techniques? Key specifications?
6. **Findings** — Main results? Key coefficient estimates and standard errors?
7. **Contributions** — What is learned that we didn't know before?
8. **Replication feasibility** — Public data? Replication archive? Data appendix? URLs?

---

## Key Features

### Conversion backend: marker

The conversion backend is **marker** (`marker-pdf`). Selected after a head-to-head bake-off against docling on a representative set of empirical-economics PDFs; marker won on equation fidelity, table structure, and figure extraction quality.

Backend selection is fixed in `convert.py`. There is no runtime override — if the bake-off needs to be redone for a future backend candidate, edit the `BACKEND` constant in `convert.py` explicitly so the cache namespace and venv are regenerated cleanly.

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
To wipe the entire cache (e.g., after a backend upgrade):
```bash
rm -rf ~/.cache/claude-pdf-converter/cache/
```
The venv at `~/.cache/claude-pdf-converter/venv-marker/` is untouched.

### `_text.md` collision handling

If a `_text.md` already exists alongside the PDF (e.g., from a prior `/split-pdf` run), the skill asks whether to overwrite it or save the new extraction as `_text2.md`. This lets you compare extractions from both methods on the same paper without losing earlier work.

### Agent isolation protocol

When another skill calls `/read-pdf`, the conversion runs in the parent context (lightweight bash call) and the reading runs inside a subagent. The subagent reads `markdown.md`, writes plain-text `_text.md`, and the parent reads only the text output. This prevents the converted markdown from accumulating token cost in a busy workflow conversation.

---

## `/read-pdf` vs `/split-pdf` — When to Use Which

| | `/split-pdf` | `/read-pdf` |
|---|---|---|
| **Reading mechanism** | Claude vision-reads PDF page images | Marker converts to markdown; Claude reads text |
| **Setup required** | None | `install.py` (~500 MB, one-time) |
| **First-run latency** | None | ~1–3 min (model download + conversion) |
| **Subsequent runs** | — | Instant if cached |
| **Equation fidelity** | Good (vision-based) | Better (native LaTeX extraction) |
| **Table structure** | Good | Better (layout-aware) |
| **Works without internet** | No (unless PDF already local) | Yes (after install) |
| **Output format** | `_text.md` | `_text.md` (same format) |

Both skills produce identical `_text.md` output format and can be used interchangeably by downstream skills like `/bib-update` and `/wiki-update`.

---

## Limitations

- **Requires local setup.** First run downloads ~500 MB of models. Not suitable for environments where you can't write to `~/.cache/`.
- **Conversion can fail on malformed PDFs.** If `convert.py` errors, the skill stops — it does not fall back to a degraded alternative. Fix the PDF or use `/split-pdf` instead.
- **Not for triage.** If you just need to decide whether a paper is relevant, use `/split-pdf` (no setup, works immediately on first split).

---

## Acknowledgments

The in-place PDF handling, persistent `_text.md` extraction, build directory convention, and agent isolation protocol follow conventions established in the `/split-pdf` skill, where they were inspired by improvements identified by [Ben Bentzin](https://www.mccombs.utexas.edu) (Associate Professor of Instruction, McCombs School of Business, University of Texas at Austin). The marker integration (`convert.py`, `install.py`) and content-hash caching design are original to this skill.
