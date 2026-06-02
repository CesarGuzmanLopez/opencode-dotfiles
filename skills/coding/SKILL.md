---
name: coding
description: General-purpose coding instructions for all coding agents.
---
Available: ruff, git, pdf, web-search, arxiv, playwright, sequential-thinking, memory, comby-search, comby-replace.

Workflow: read code → plan → implement → **MUST ruff check** → test → commit.

Rules:
- **ALWAYS run ruff check on modified Python files.** This is mandatory, not optional.
- If ruff finds errors, fix them before proceeding.
- Only skip ruff check if the file is not Python.
- Use git for version control.
- Prefer minimal focused changes.
- Never leave dead code.
