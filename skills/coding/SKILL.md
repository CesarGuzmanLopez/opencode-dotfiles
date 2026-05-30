---
name: coding
description: General-purpose coding instructions for all coding agents.
---
Available MCPs: ruff, git, pdf, duckduckgo, fetch, arxiv, puppeteer/playwright, sequential-thinking, memory, filesystem.
Also available: comby-search, comby-replace for structural code search and replacement.

Workflow: read code → plan → implement → **MUST ruff check** → test → commit.

Rules:
- **ALWAYS run ruff check on modified Python files.** This is mandatory, not optional.
- If ruff finds errors, fix them before proceeding.
- Only skip ruff check if the file is not Python.
- Use git for version control.
- Prefer minimal focused changes.
- Never leave dead code.
