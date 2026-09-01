# `/read-pdf` — Download, Convert, and Deep-Read Academic Papers

**Same workflow as `/split-pdf`, but uses python:marker to convert the PDF to markdown locally first, instead of having Claude vision-read PDF page images.** This makes equation, table, and figure extraction more faithful, and avoids image-based context bloat in the parent conversation.

**Skill location:** [`.claude/skills/read-pdf/SKILL.md`](../../.claude/skills/read-pdf/SKILL.md)

---

## What This Skill Does

You give Claude a paper — either a local PDF file or a search query — and it does the rest. It finds and downloads the paper, or uses your local file in place, converts it to clean markdown using python:marker, then reads that markdown to write structured notes. When finished, it saves a persistent `_text.md` extraction alongside the source PDF, in the same format produced by `/split-pdf`.

---

## Why It Exists

`/split-pdf` reads PDFs by having Claude vision-read page images in batches. This works well for most papers but has two limitations:

1. **Equation fidelity.** PDF page images render math as bitmaps. Vision-reading bitmaps produces approximate LaTeX transcriptions. Papers heavy with structural equations benefit from native math extraction.
2. **Table structure.** Complex tables are harder to transcribe accurately from images than from a layout-aware text conversion.

`/read-pdf` addresses both by running a local conversion step first. The result is a `markdown.md` file where equations are native LaTeX math mode and tables are pipe-syntax markdown — readable as text rather than image bitmaps.

---

## How It Works

```
~/.cache/claude-pdf-converter/
├── venv-marker/                         # one-time install of marker-pdf
└── cache/
    └── marker/
        └── <sha256-of-pdf>/
            ├── markdown.md              # conversion + inline ![](figures/...)
            ├── figures/
            │   ├── fig_1.png
            │   └── fig_2.png
            └── meta.json                # backend, page/figure counts, timestamp
```

| Step | Action |
|------|--------|
| **Acquire** | Download the PDF via web search or use a local file in place |
| **Install** | `install.py` sets up the marker venv on first run (~500 MB, one-time) |
| **Check cache** | SHA-256 hash check — skip re-conversion if markdown already exists |
| **Convert** | `convert.py` runs marker and writes `markdown.md` to the content-hash cache |
| **Collision** | If `_text.md` already exists, ask: overwrite or save as `_text2.md`? |
| **Extract** | Read `markdown.md`, write bibliographic metadata + 8-dimension notes |
| **Persist** | Save final extraction to `<basename>_text.md` alongside the source PDF |

### Usage

```
/read-pdf path/to/paper.pdf
/read-pdf "Gentzkow Shapiro Sinkinson 2014 competition newspapers"
```

When called by another skill, the caller can invoke `convert.py` directly via bash rather than spawning `/read-pdf` as a slash command — the script is the conversion contract.

### First-run cost

The first invocation on a fresh machine creates a venv at `~/.cache/claude-pdf-converter/venv-marker/` and downloads marker's layout/OCR models (~500 MB, 1–3 min). The skill prints a one-line warning so the user knows why it is slow. Every subsequent invocation skips this setup entirely.

The venv lives **outside any git repo** so the model files do not pollute a checkout.

---

## Conversion Backend

The backend is fixed to **marker** (`marker-pdf`). Marker was selected after a bake-off on empirical-economics PDFs because it performed well on equation fidelity, table structure, and figure extraction quality.

Backend selection is not exposed as a runtime option. If a future backend candidate should replace marker, edit the `BACKEND` constant in `convert.py` so the cache namespace and venv are regenerated cleanly.

### Born-digital PDFs and OCR

Most journal PDFs already contain an embedded text layer. For those files, `convert.py` samples the first pages with `pdftotext` and tells marker to use the embedded text rather than re-OCRing the whole document. Marker still performs layout, table, and selected region recognition, but avoids the slow full-document OCR path. If the text-layer sample is missing or too sparse, marker keeps OCR enabled for scanned PDFs.

### GPU acceleration

Auto-detected: NVIDIA CUDA → CPU. MPS on Apple Silicon is excluded because surya's layout model crashes at runtime on MPS with an index-bounds error. No flags are needed on any platform.

---

## Output Contract

`/read-pdf` writes the same `_text.md` format as `/split-pdf`: a bibliographic metadata block followed by eight research-note dimensions.

```
## Bibliographic metadata
doi: <10.xxxx/yyyy or null>
authors: [LastName1, LastName2, ...]
title: <verbatim title>
year: <year>
venue: <journal/working paper series/etc.>
venue_type: journal | working_paper | book_chapter | other
```

This means downstream skills like `/bib-update` and `/wiki-update` can consume outputs from either `/split-pdf` or `/read-pdf`.

---

## Failure Mode

Hard fail. If marker errors on a given PDF (encrypted, malformed, OCR fails), the script exits non-zero and the caller surfaces the error. There is no silent fallback to `pdftotext` or any other tool — silent fallbacks can produce wrong conversions that look plausible on inspection.

---

## Limitations

- **First-run is slow** — venv creation + model download takes 1–3 minutes. After that, conversion of a typical 30-page paper takes ~30s–2min depending on hardware.
- **Requires writable cache space** at `~/.cache/claude-pdf-converter/`.
- **Conversion can fail on malformed PDFs.** If `convert.py` errors, use `/split-pdf` instead.
- **Cache is not auto-evicted** — re-converting the same PDF is free, but the cache grows monotonically. Wipe with `rm -rf ~/.cache/claude-pdf-converter/cache/` if needed.

---

## Acknowledgments

The in-place PDF handling, persistent `_text.md` extraction, build directory convention, and agent isolation protocol follow conventions established in the `/split-pdf` skill, where they were inspired by improvements identified by [Ben Bentzin](https://www.mccombs.utexas.edu) (Associate Professor of Instruction, McCombs School of Business, University of Texas at Austin). The marker integration (`convert.py`, `install.py`) and content-hash caching design are original to this skill.
