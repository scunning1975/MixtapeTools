# `/split-pdf` — Download, Split, and Deep-Read Academic Papers

**Skill location:** [`.claude/skills/split-pdf/SKILL.md`](../../.claude/skills/split-pdf/SKILL.md)

---

## What This Skill Does

You give Claude a paper — either a local PDF file or a search query like "Gentzkow Shapiro 2014 competition newspapers" — and it does the rest. It finds the paper online and downloads it (or uses your local file in place), splits it into 4-page chunks using PyPDF2, then reads those chunks in small batches (3 at a time, ~12 pages), pausing between each batch for your review. As it reads, it writes structured notes into a `notes.md` file, extracting a bibliographic metadata block plus eight research dimensions. When finished, it saves a persistent `_text.md` extraction alongside the source PDF so future invocations can skip re-reading entirely.

---

## Why It Exists

Claude Code can read PDFs, but long academic papers cause two failures:

1. **Session crash.** PDFs are token-expensive (fonts, vector graphics, tables, math notation). A 40-page paper can exceed the context window, producing an unrecoverable "prompt too long" error that destroys the entire session and all context.

2. **Shallow reading.** Even when the PDF fits, Claude's attention degrades over long documents — it reads the abstract carefully, skims the methodology, and often hallucinates details from the results. You get a confident summary that's subtly wrong.

These are related but distinct problems. The first kills the session. The second produces unreliable output while the session continues normally. Splitting addresses both.

---

## The Solution

Split the PDF into 4-page chunks, read 3 chunks at a time (~12 pages), and write structured notes incrementally.

### How It Works

| Step | Action |
|------|--------|
| **Acquire** | Download the PDF (via web search) or use a local file in place |
| **Check** | Look for existing `_text.md` extract or existing splits — offer to reuse |
| **Split** | PyPDF2 splits into 4-page chunks in `<foldername>_build/split_<name>/` |
| **Read** | Read 3 splits at a time, pause after each batch |
| **Extract** | Update running `notes.md` with structured information |
| **Persist** | Save final extraction to `<basename>_text.md` alongside the source PDF |
| **Confirm** | Wait for user approval before continuing to next batch |

### Usage

```
/split-pdf path/to/paper.pdf
/split-pdf "Gentzkow Shapiro Sinkinson 2014 competition newspapers"
```

**You must tell Claude what paper to read.** Claude cannot webcrawl for a paper it doesn't know exists. Provide either a local file path or a search query specific enough to find the paper — an author name, title, keywords, year, or some combination. If you just type `/split-pdf` with nothing else, Claude will ask you what you're looking for.

### What Gets Extracted

The skill produces a **structured extraction** — more detailed and specific than a typical summary. It starts with a `## Bibliographic metadata` block, then records the dimensions a researcher needs to build on or replicate the work:

0. **Bibliographic metadata** — DOI, authors, title, year, venue, and venue type when visible on the title page
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

### In-place PDF handling

The skill uses the PDF wherever it already lives. No copying to a centralized `articles/` folder. This lets the skill work inside any project folder without rearranging your file structure.

### Persistent extraction (`_text.md`)

After all batches are read, the skill writes a structured plain-text extraction as `<basename>_text.md` next to the source PDF. On future invocations, the skill checks for this file first and offers to reuse it — skipping re-reading entirely. This saves tokens and time on previously processed papers.

### Split reuse

If splits already exist in the build directory from a previous run, the skill offers to reuse them instead of re-splitting.

### Build directory convention

Splits go into `<foldername>_build/split_<basename>/` rather than directly alongside the PDF. This keeps working artifacts (splits, intermediate notes) separate from source files and finished outputs. Multiple PDFs in the same folder share one build directory.

### Agent isolation protocol

When another skill calls `/split-pdf` (for example, `/beautiful_deck` reading a paper before generating slides), the PDF reading runs inside a subagent. Each PDF page renders as image data that accumulates permanently in the conversation context. A 35-page paper can add 10-20MB. Without isolation, two or three large PDFs crash the session by hitting the API request size limit. The subagent reads the pages, writes plain-text output, and the parent skill only reads the text.

Standalone invocations (user calls `/split-pdf` directly) use the interactive pause-and-confirm protocol in the main conversation.

---

## Why This Design

**Why 4-page chunks?** Small enough for careful attention, large enough to keep logical sections (a methodology subsection, a results table with discussion) together. A 40-page paper becomes 10 chunks read in 4 rounds.

**Why 3 chunks per batch (~12 pages)?** Balances throughput against attention quality. Twelve pages is enough to make progress but not so much that comprehension degrades.

**Why pause between batches?** So you can:
- Review intermediate output and catch errors before they compound
- Redirect the reading or ask follow-up questions
- Skip sections that aren't relevant
- Control pacing for sections that need more care

**Why incremental notes instead of a final summary?** When Claude reads a full paper at once, it produces a summary — lossy compression. When it reads in batches and updates running notes, it accumulates detail. The final notes are richer than any one-shot summary.

**Why persist the extraction?** A 40-page paper costs ~4 rounds of PDF image rendering. Doing that twice is waste. The `_text.md` file lets you come back to the paper weeks later without re-reading a single page.

For the full methodology, see [`.claude/skills/split-pdf/methodology.md`](../../.claude/skills/split-pdf/methodology.md).

---

## Directory Structure After Running

```
articles/                             # any working folder
├── smith_2024.pdf                    # original PDF — ALWAYS preserved, never deleted
├── smith_2024_text.md                # structured extract — reusable across sessions
└── articles_build/                   # <foldername>_build/ — shared build folder
    └── split_smith_2024/             # split_<pdf-basename>/
        ├── smith_2024_pp1-4.pdf      # 4-page chunks
        ├── smith_2024_pp5-8.pdf
        ├── smith_2024_pp9-12.pdf
        ├── ...
        └── notes.md                  # working copy of structured notes
```

**The original PDF is never deleted.** Whether Claude downloaded it via web search or you pointed it to a local file, the original always stays where it was. The split files are derivatives. If anything goes wrong — a corrupted split, a re-read with different parameters — you can always re-split from the original.

---

## Limitations

- **It is slow.** A 37-page paper requires ~4 rounds of reading with user confirmation between each. This is a deliberate trade-off: careful reading over fast reading.
- **Notes can become repetitive** if the paper revisits themes. Some manual editing of the final notes may be useful.
- **Not for triage.** If you just need to decide whether a paper is relevant, read only the first split (pages 1-4, which usually contains the abstract and introduction). You don't need the full protocol.
- **Papers under ~15 pages** can be read directly without splitting.

---

## Acknowledgments

The in-place PDF handling, persistent `_text.md` extraction, split reuse, build directory convention, and agent isolation protocol were inspired by improvements identified by [Ben Bentzin](https://www.mccombs.utexas.edu) (Associate Professor of Instruction, McCombs School of Business, University of Texas at Austin), who adapted the original skill for his own workflows and shared his findings (April 2026). His version demonstrated that subagent isolation prevents context bloat when reading multiple large PDFs in a single session — a critical reliability improvement. The implementation here is independently written but the ideas are his.
