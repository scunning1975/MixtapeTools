---
name: split-pdf
description: Compatibility wrapper for `/read-pdf --split`. Use only when the user explicitly invokes `/split-pdf` or asks for the legacy split-PDF vision-batch workflow. For new paper-reading requests, prefer `/read-pdf`; use `/read-pdf --split` for triage, converter failures, or no marker setup.
allowed-tools: Bash(python*), Bash(pip*), Bash(curl*), Bash(wget*), Bash(mkdir*), Bash(ls*), Read, Write, Edit, WebSearch, WebFetch, Agent
argument-hint: [pdf-path-or-search-query]
---

# Split-PDF Compatibility Wrapper

This skill is retained for existing slash-command muscle memory. Execute the request as:

```text
/read-pdf --split <same arguments>
```

Follow `.claude/skills/read-pdf/SKILL.md`, specifically the `--split` mode branch.

Compatibility notes:

- The original PDF is preserved.
- Split files still use `<foldername>_build/split_<basename>/`.
- The output remains `<basename>_text.md` with the same bibliographic metadata block and 8 research dimensions.
- For subagent isolation, use `.claude/skills/read-pdf/isolation_split.md`.
