# Extraction Schema

The structured-extraction contract shared by `/read-pdf` default mode, `/read-pdf --split` mode, and downstream `wiki-update` marker ingest. Output is a single project-neutral markdown file (`<basename>_text.md`) consisting of an optional title, a bibliographic metadata block, plain-English synthesis, and research notes in that order. The bibliographic metadata block must not appear after the research dimensions.

## Bibliographic metadata (always first)

From the title page (or title section of the converted markdown), extract:

```
## Bibliographic metadata
doi: <10.xxxx/yyyy if present on the title page, else null>
authors: [LastName1, LastName2, ...]
title: <verbatim title from title page>
year: <year>
venue: <journal/working paper series/etc., verbatim>
venue_type: journal | working_paper | book_chapter | other
```

If a field is not visible on the title page, record `null`. Do not guess.

## Plain-English synthesis

Hard cap: ~200 words. No jargon. Cover the research question, why it matters, what the paper estimates and how in plain terms, what it finds, and the main take-away.

## Research dimensions

1. **Research question** — What is the paper asking and why does it matter?
2. **Audience** — Which sub-community of researchers cares about this?
3. **Method** — How do they answer the question? What is the identification strategy?
4. **Target parameter** — What estimand or causal/statistical object is being targeted?
5. **Data** — What data do they use? Where precisely did they find it? What is the unit of observation? Sample size? Time period?
6. **Statistical methods / specifications** — What econometric or statistical techniques do they use? What are the key specifications?
7. **Findings** — What are the main results? Key coefficient estimates and standard errors?
8. **Contributions** — What is learned from this exercise that we didn't know before?
9. **Replication feasibility** — Is the data publicly available? Is there a replication archive? A data appendix? URLs for the underlying data?
10. **Tables** — Inventory tables, extracting machine-readable tables when central to understanding or replication.
11. **Figures** — Inventory figures, captions, and key visual claims.
12. **Equations / formal objects** — Inventory equations, formal models, propositions, algorithms, and labeled specifications.

## Tone

A structured extraction more detailed and specific than a typical summary — what a researcher needs to **build on or replicate** the work. By the time the extraction is finished, the notes should contain specific data sources, variable names, equation references, sample sizes, coefficient estimates, and standard errors. Not a summary — a structured extraction.
