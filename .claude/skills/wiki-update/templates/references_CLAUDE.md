# LLM Wiki

A personal knowledge base maintained by Claude Code.
Based on [Andrej Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

## Purpose

This wiki is a structured, interlinked knowledge base for the {{PROJECT_NAME}} research project.
Claude maintains the wiki. The human curates sources, asks questions, and guides the analysis.

## Folder structure

```
raw/             -- source documents (immutable -- never modify these)
wiki/            -- markdown pages maintained by Claude
wiki/index.md    -- table of contents for the entire wiki
wiki/log.md      -- append-only record of all operations
wiki/figures/    -- extracted figure clips from source PDFs
```

## Ingest workflow

When the user adds a new source to `raw/` and asks you to ingest it:

1. Read the full source document (via `/wiki-update`'s converter for PDFs, if available)
2. Discuss key takeaways with the user before writing anything
3. Create a summary page in `wiki/` named after the source
4. Create or update concept pages for each major idea or entity
5. Add wiki-links ([[page-name]]) to connect related pages
6. Update `wiki/index.md` with new pages and one-line descriptions
7. Append an entry to `wiki/log.md` with the date, source name, and what changed

A single source may touch 10-15 wiki pages. That is normal.

## Page format

Every wiki page should follow this structure:

```markdown
# Page Title

**Summary**: One to two sentences describing this page.

**Sources**: List of raw source files this page draws from.

**Last updated**: Date of most recent update.

---

Main content goes here. Use clear headings and short paragraphs.

Link to related concepts using [[wiki-links]] throughout the text.

## Related pages

- [[related-concept-1]]
- [[related-concept-2]]
```

## Math notation

Always write math in LaTeX/Markdown math mode, **never** as Unicode symbols or plaintext.

- Inline math → `$x_{it}$`, `$\beta^S - \beta^N$`, `$\epsilon_t$`
- Display math → `$$ ... $$` on its own line
- Greek letters, subscripts, superscripts, operators (≤, ≥, ∑, ∫, ≈) all go inside `$...$`, never as Unicode

This applies to every wiki page, every extraction note, and every string Claude writes into this wiki. Unicode math is hard to read, impossible to copy into a .tex file, and inconsistent across pages.

## Citation rules

- Every factual claim should reference its source file
- Use the format (source: filename.pdf) after the claim
- If two sources disagree, note the contradiction explicitly
- If a claim has no source, mark it as needing verification

## Question answering

When the user asks a question:

1. Read `wiki/index.md` first to find relevant pages
2. Read those pages and synthesize an answer
3. Cite specific wiki pages in your response
4. If the answer is not in the wiki, say so clearly
5. If the answer is valuable, offer to save it as a new wiki page

Good answers should be filed back into the wiki so they compound over time.

## Lint

When the user asks you to lint or audit the wiki:

- Check for contradictions between pages
- Find orphan pages (no inbound links from other pages)
- Identify concepts mentioned in pages that lack their own page
- Flag claims that may be outdated based on newer sources
- Check that all pages follow the page format above
- Report findings as a numbered list with suggested fixes

## Rules

- Never modify anything in the `raw/` folder
- Always update `wiki/index.md` and `wiki/log.md` after changes
- Keep page names lowercase with hyphens (e.g. `machine-learning.md`)
- Write in clear, plain language
- When uncertain about how to categorize something, ask the user
