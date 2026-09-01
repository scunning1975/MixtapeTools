---
name: read-pdf
description: Download or use a local academic PDF, convert to clean markdown locally (python:marker, layout-aware), then extract structured reading notes into `_text.md`. Same output contract as /split-pdf — bibliographic metadata block + 8-dimension research notes — but uses local conversion instead of Claude vision-reading PDF images. Preserves equation fidelity, table structure, and figure references. Use when you want higher-fidelity math/table extraction, or when you already have a local file.
allowed-tools: Bash(python3:*), Bash(curl:*), Bash(wget:*), Bash(mkdir:*), Read, Write, WebSearch, WebFetch, Agent
argument-hint: [pdf-path-or-search-query]
---

# Read-PDF: Download, Convert, and Deep-Read Academic Papers

Same I/O contract as /split-pdf: takes a PDF (local or searched), produces a structured `_text.md` extraction with a bibliographic metadata block and 8-dimension research notes. The difference is the reading mechanism: instead of Claude vision-reading PDF page images in chunks, read-pdf converts the PDF to markdown locally using python:marker, then reads the text. This preserves equation fidelity, table structure, and figure references without image-based context bloat.

## When This Skill Is Invoked

The user wants to read, review, or summarize an academic paper and either: (a) wants layout-aware equation/table extraction, or (b) already has a local PDF. The input is either:
- A file path to a local PDF (e.g., `~/Documents/papers/smith_2024.pdf`)
- A search query or paper title (e.g., `"Gentzkow Shapiro Sinkinson 2014 competition newspapers"`)

**Important:** You cannot search for a paper you don't know exists. Provide either a file path or a specific query. If the user invokes this skill without specifying a paper, ask them.

## Prerequisites

- **Python ≥ 3.10** must be available. `install.py` refuses to proceed on Python 3.9 or older. If needed: `brew install python@3.12`, `apt install python3.11`, or python.org installer.
- **Optional GPU acceleration** is auto-detected: NVIDIA CUDA → CPU. (MPS on Apple Silicon is excluded — surya's layout model crashes on MPS at runtime.)

## Step 1: Acquire the PDF

**If a local file path is provided:**
- Verify the file exists
- Use the PDF in place. The working directory is the folder containing the PDF.
- Proceed to Step 2

**If a search query or paper title is provided:**
1. Use WebSearch to find the paper
2. Use WebFetch or Bash (curl/wget) to download the PDF
3. Save it to the current working directory
4. Proceed to Step 2

**CRITICAL: Always preserve the original PDF.** Never delete, move, or overwrite it at any point in this workflow.

## Step 2: Ensure the converter is installed

```bash
python3 ~/.claude/skills/read-pdf/install.py
```

Idempotent. First run creates a venv at `~/.cache/claude-pdf-converter/venv-marker/` and downloads marker models (~500 MB, 1–3 min). Surface the "First run" message to the user verbatim if it appears — they should know why this invocation is slow.

## Step 3: Convert

**Before converting, check for a cached conversion.** Compute the SHA-256 hash of the PDF and check whether `markdown.md` already exists in the cache:

```python
import hashlib, os, sys

pdf_path = "<absolute-pdf-path>"

with open(pdf_path, 'rb') as f:
    pdf_hash = hashlib.sha256(f.read()).hexdigest()

markdown_path = os.path.expanduser(
    f'~/.cache/claude-pdf-converter/cache/marker/{pdf_hash}/markdown.md'
)
print(markdown_path if os.path.exists(markdown_path) else "NOT_CACHED")
```

- **If cached:** tell the user "Using cached markdown conversion (SHA-256 match), skipping re-conversion." Use the printed path as `markdown_path`.
- **If not cached:** run:
  ```bash
  python3 ~/.claude/skills/read-pdf/convert.py "<pdf-path>"
  ```
  It prints the absolute path to `markdown.md` on success and exits 0. For born-digital PDFs with a usable embedded text layer, `convert.py` uses that text layer and disables marker's full-document OCR path while preserving marker's layout/table processing. **Do not fall back to pdftotext or any other tool on failure** — surface the error and stop. The whole point of this skill is the layout-aware conversion; a degraded fallback produces silently-wrong output.

## Step 4: Check for existing `_text.md`

Look for `<basename>_text.md` in the same folder as the PDF.

If found, ask:
> "An extract already exists (`<basename>_text.md`). Overwrite it, or save the new extraction as `<basename>_text2.md`?"

Proceed using whichever filename the user chooses.

## Step 5: Structured Extraction

Read `markdown.md` and collect information along these dimensions:

0. **Bibliographic metadata** — From the title section of the markdown, extract:
   ```
   ## Bibliographic metadata
   doi: <10.xxxx/yyyy if present, else null>
   authors: [LastName1, LastName2, ...]
   title: <verbatim title>
   year: <year>
   venue: <journal/working paper series/etc., verbatim>
   venue_type: journal | working_paper | book_chapter | other
   ```
   If a field is not visible, record `null`.

1. **Research question** — What is the paper asking and why does it matter?
2. **Audience** — Which sub-community of researchers cares about this?
3. **Method** — How do they answer the question? What is the identification strategy?
4. **Data** — What data do they use? Where precisely did they find it? Unit of observation? Sample size? Time period?
5. **Statistical methods** — What econometric or statistical techniques? Key specifications?
6. **Findings** — Main results? Key coefficient estimates and standard errors?
7. **Contributions** — What is learned that we didn't know before?
8. **Replication feasibility** — Public data? Replication archive? Data appendix? URLs?

## The Output File

Write the final structured extraction to `<basename>_text.md` (or `_text2.md` if chosen in Step 4) in the same folder as the source PDF, with the `## Bibliographic metadata` block first, followed by the research notes.

Notify the user:
> "Extract saved to `smith_2024_text.md` alongside the source PDF. Future requests on this paper can reuse it without re-reading."

This file is the persistent, reusable artifact.

## Agent Isolation Protocol

**When read-pdf is invoked by another skill**, the conversion steps (Steps 2–3) run in the parent context — they are lightweight bash calls. The reading and extraction (Steps 4–5) MUST run inside a subagent. The converted `markdown.md` can be large, and reading it in the parent context of an active workflow accumulates permanent token cost. The subagent reads `markdown.md`, writes plain-text `_text.md`, and the parent reads only that.

**Pattern:**

The parent skill handles install.py, the SHA-256 cache check, convert.py if needed, and the `_text.md` collision check. Then it launches an Agent:

```
Read a converted markdown file and produce structured extraction notes.

Markdown input: <markdown_path>
Text output: <text_path>

Process:
1. Read <markdown_path> using the Read tool
2. From the title section, extract a bibliographic metadata block:
   ## Bibliographic metadata
   doi: <10.xxxx/yyyy if present, else null>
   authors: [LastName1, LastName2, ...]
   title: <verbatim title>
   year: <year>
   venue: <journal/working paper series/etc., verbatim>
   venue_type: journal | working_paper | book_chapter | other
3. Extract: research question, audience, method, data (sources, sample size, time period),
   statistical methods, findings, contributions, replication feasibility
4. Write the final structured extraction to <text_path>, with the
   ## Bibliographic metadata block first, followed by the research notes.

Report when done: page count, figures/tables found, one-sentence content summary.
```

After the agent returns, the parent reads `_text.md` (plain text, not the large `markdown.md`) and continues its workflow.

**Standalone invocations** (user calls `/read-pdf` directly) read `markdown.md` in the main conversation and write `_text.md` directly — no subagent needed for a one-off read.

## Quick Reference

| Step | Action |
|------|--------|
| **Acquire** | Download via web search or use local file in place |
| **Install** | `python3 ~/.claude/skills/read-pdf/install.py` (idempotent; downloads models on first run) |
| **Check cache** | SHA-256 → `~/.cache/claude-pdf-converter/cache/marker/<hash>/markdown.md` |
| **Convert** | `python3 ~/.claude/skills/read-pdf/convert.py <pdf>` if not cached |
| **Collision** | Ask overwrite vs `_text2.md` if `_text.md` already exists |
| **Extract** | Bibliographic metadata + 8-dimension notes from `markdown.md` |
| **Persist** | Save to `<basename>_text.md` alongside the source PDF |

For backend details, cache management, and GPU notes, see [README.md](README.md).
