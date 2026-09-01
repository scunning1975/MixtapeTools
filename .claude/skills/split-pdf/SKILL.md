---
name: split-pdf
description: Download, split, and deeply read academic PDFs. Use when asked to read, review, or summarize an academic paper. Splits PDFs into 4-page chunks, reads them in small batches, and produces structured reading notes — avoiding context window crashes and shallow comprehension.
allowed-tools: Bash(python*), Bash(pip*), Bash(curl*), Bash(wget*), Bash(mkdir*), Bash(ls*), Read, Write, Edit, WebSearch, WebFetch, Agent
argument-hint: [pdf-path-or-search-query]
---

# Split-PDF: Download, Split, and Deep-Read Academic Papers

**CRITICAL RULE: Never read a full PDF. Never.** Only read the 4-page split files, and only 3 splits at a time (~12 pages). Reading a full PDF will either crash the session with an unrecoverable "prompt too long" error — destroying all context — or produce shallow, hallucinated output. There are no exceptions.

## When This Skill Is Invoked

The user wants you to read, review, or summarize an academic paper. The input is either:
- A file path to a local PDF (e.g., `~/Documents/papers/smith_2024.pdf`)
- A search query or paper title (e.g., `"Gentzkow Shapiro Sinkinson 2014 competition newspapers"`)

**Important:** You cannot search for a paper you don't know exists. The user MUST provide either a file path or a specific search query — an author name, a title, keywords, a year, or some combination that identifies the paper. If the user invokes this skill without specifying what paper to read, ask them. Do not guess.

## Step 1: Acquire the PDF

**If a local file path is provided:**
- Verify the file exists
- Use the PDF in place. The working directory is the folder containing the PDF.
- Proceed to Step 2

**If a search query or paper title is provided:**
1. Use WebSearch to find the paper
2. Use WebFetch or Bash (curl/wget) to download the PDF
3. Save it to the current working directory (create the directory if needed)
4. Proceed to Step 2

**CRITICAL: Always preserve the original PDF.** The source PDF must NEVER be deleted, moved, or overwritten at any point in this workflow. The split files are derivatives; the original is the permanent artifact. Do not clean up, do not remove, do not tidy. The original stays.

## Step 2: Split the PDF

**Before splitting, check for an existing extract.** Look for `<basename>_text.md` in the same folder as the PDF.

If found, ask:
> "An extract from a previous deep-read exists (`<basename>_text.md`). Use it for this request, or re-read the PDF from scratch?"
- **Use extract**: read `<basename>_text.md` and use it as the source notes — skip the rest of Steps 2 and 3 entirely
- **Re-read**: proceed with splitting below

This prevents redundant re-reading of papers you have already processed. The `_text.md` file is a structured plain-text extraction that is far cheaper to read than re-processing the PDF page images.

**If no extract exists, check for existing splits.** Determine the build directory:

```python
import os
folder_path = os.path.dirname(os.path.abspath(pdf_path))
foldername  = os.path.basename(folder_path)
pdf_basename = os.path.splitext(os.path.basename(pdf_path))[0]
build_dir = os.path.join(folder_path, foldername + '_build')
split_dir = os.path.join(build_dir, 'split_' + pdf_basename)
```

If `split_dir` already exists and contains `.pdf` files, ask:
> "Splits already exist for `<pdf-basename>` (N chunks in `<foldername>_build/split_<pdf-basename>/`). Reuse existing splits, or re-split from scratch?"
- **Reuse**: skip splitting, proceed to Step 3 using the existing files in `split_dir`
- **Re-split**: delete the existing split folder, then proceed with splitting below

Create splits in `<foldername>_build/split_<pdf-basename>/` and run the splitting script:

```python
from PyPDF2 import PdfReader, PdfWriter
import os, sys

def split_pdf(input_path, output_dir, pages_per_chunk=4):
    os.makedirs(output_dir, exist_ok=True)
    reader = PdfReader(input_path)
    total = len(reader.pages)
    prefix = os.path.splitext(os.path.basename(input_path))[0]

    for start in range(0, total, pages_per_chunk):
        end = min(start + pages_per_chunk, total)
        writer = PdfWriter()
        for i in range(start, end):
            writer.add_page(reader.pages[i])

        out_name = f"{prefix}_pp{start+1}-{end}.pdf"
        out_path = os.path.join(output_dir, out_name)
        with open(out_path, "wb") as f:
            writer.write(f)

    print(f"Split {total} pages into {-(-total // pages_per_chunk)} chunks in {output_dir}")
```

**Directory convention:**
```
articles/                             # any working folder
├── smith_2024.pdf                    # original PDF — NEVER DELETE THIS
├── smith_2024_text.md                # structured extract — created after deep-read
└── articles_build/                   # <foldername>_build/ — shared build folder
    └── split_smith_2024/             # split_<pdf-basename>/
        ├── smith_2024_pp1-4.pdf
        ├── smith_2024_pp5-8.pdf
        ├── smith_2024_pp9-12.pdf
        ├── notes.md                  # working copy — source for _text.md
        └── ...
```

The build directory convention (`<foldername>_build/`) keeps split artifacts, compilation intermediates, and other working files separate from the source material and finished outputs. Multiple PDFs in the same folder share one build directory, each with its own `split_<basename>/` subdirectory inside it.

The original PDF remains permanently. The splits are working copies. If anything goes wrong, you can always re-split from the original.

If PyPDF2 is not installed, install it: `pip install PyPDF2`

## Step 3: Read in Batches of 3 Splits

Read **exactly 3 split files at a time** (~12 pages). After each batch:

1. **Read** the 3 split PDFs using the Read tool
2. **Update** the running notes file (`notes.md` in the split subdirectory)
3. **Pause** and tell the user:

> "I have finished reading splits [X-Y] and updated the notes. I have [N] more splits remaining. Would you like me to continue with the next 3?"

4. **Wait** for the user to confirm before reading the next batch

Do NOT read ahead. Do NOT read all splits at once. The pause-and-confirm protocol is mandatory.

## Step 4: Structured Extraction

As you read, collect information along these dimensions and write them into `notes.md`:

0. **Bibliographic metadata** — From the first split (title page), extract:
   ```
   ## Bibliographic metadata
   doi: <10.xxxx/yyyy if present on the title page, else null>
   authors: [LastName1, LastName2, ...]
   title: <verbatim title from title page>
   year: <year>
   venue: <journal/working paper series/etc., verbatim>
   venue_type: journal | working_paper | book_chapter | other
   ```
   If a field is not visible on the title page, record `null`.

1. **Research question** — What is the paper asking and why does it matter?
2. **Audience** — Which sub-community of researchers cares about this?
3. **Method** — How do they answer the question? What is the identification strategy?
4. **Data** — What data do they use? Where precisely did they find it? What is the unit of observation? Sample size? Time period?
5. **Statistical methods** — What econometric or statistical techniques do they use? What are the key specifications?
6. **Findings** — What are the main results? Key coefficient estimates and standard errors?
7. **Contributions** — What is learned from this exercise that we didn't know before?
8. **Replication feasibility** — Is the data publicly available? Is there a replication archive? A data appendix? URLs for the underlying data?

These questions extract what a researcher needs to **build on or replicate** the work — a structured extraction more detailed and specific than a typical summary.

## The Notes File

The working notes file is `notes.md` in the split subdirectory, updated incrementally after each batch. Structure it with clear headers for the bibliographic metadata block and each of the eight research dimensions. After each batch, update whichever dimensions have new information — do not rewrite from scratch.

By the time all splits are read, the notes should contain specific data sources, variable names, equation references, sample sizes, coefficient estimates, and standard errors. Not a summary — a structured extraction.

**After all batches are complete**, write the final notes to `<basename>_text.md` in the same folder as the source PDF, with the `## Bibliographic metadata` block first:

```
articles/smith_2024_text.md
```

Then notify the user:
> "Extract saved to `smith_2024_text.md` alongside the source PDF. Future requests on this paper can reuse it without re-reading."

This file is the persistent, reusable artifact. The `notes.md` in the build directory is the working copy. Both are kept — never delete either.

## Agent Isolation Protocol

**When split-pdf is invoked by another skill or workflow** (any process that continues working after the PDF has been read), the PDF reading MUST run inside a subagent to prevent context bloat in the parent conversation.

**Why:** Each PDF page rendered by the Read tool produces image data in the conversation context. A 35-page PDF (9 chunks) can add 10-20MB of image data that accumulates permanently. After reading one or two large PDFs on top of prior work, the conversation hits the API request size limit and becomes unrecoverable: no subsequent Read calls succeed, and rewinding does not free sufficient space.

**Pattern:**

The parent skill handles splitting (Step 2's Python script) in its own context; this is lightweight. Then it launches an Agent to perform all the reading:

```
Read PDF split files and produce structured extraction notes.

Split directory: <split_dir>
Files (read in this order, 3 at a time): <file_list>
Notes output: <notes_path>
Text output: <text_path>

Process:
1. Read 3 PDF files at a time using the Read tool
2. After each batch, update the notes file with extracted content
3. From the first split (title page), extract a bibliographic metadata block:
   ## Bibliographic metadata
   doi: <10.xxxx/yyyy if present on the title page, else null>
   authors: [LastName1, LastName2, ...]
   title: <verbatim title from title page>
   year: <year>
   venue: <journal/working paper series/etc., verbatim>
   venue_type: journal | working_paper | book_chapter | other
4. Extract: research question, audience, method, data (sources, sample size, time period),
   statistical methods, findings, contributions, replication feasibility
5. Write the final structured extraction to the text output path, with the
   ## Bibliographic metadata block first, followed by the research notes.

Report when done: pages read, figures/tables found, one-sentence content summary.
```

After the agent returns, the parent reads the output files (plain markdown, not PDF images) and continues its workflow.

**Standalone invocations** (user calls `/split-pdf` directly) use the interactive protocol above with reads in the main conversation and the pause-and-confirm protocol.

## When NOT to Split

- Papers shorter than ~15 pages: read directly (still use the Read tool, not Bash)
- Policy briefs or non-technical documents: a rough summary is fine
- Triage only: read just the first split (pages 1-4) for abstract and introduction

## Quick Reference

| Step | Action |
|------|--------|
| **Acquire** | Download to the current working directory or use existing local file in place |
| **Check** | Look for existing `_text.md` extract or existing splits — offer to reuse |
| **Split** | 4-page chunks into `<foldername>_build/split_<pdf-basename>/` |
| **Read** | 3 splits at a time, pause after each batch |
| **Write** | Update `notes.md` with structured extraction |
| **Persist** | Save final extraction to `<basename>_text.md` alongside the source PDF |
| **Confirm** | Ask user before continuing to next batch |

For detailed explanation of why the batched-reading method works, see [methodology.md](methodology.md). Acknowledgments and credits live in [README.md](README.md).
