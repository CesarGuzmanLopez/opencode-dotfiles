---
name: scientific-research
description: Academic research: papers, chemical compounds, citations. Uses arXiv, PubChem, Crossref. Saves report to file.
---
Divide research into independent sub-tasks. Delegate each with task to save tokens.

1. Plan: break into sub-topics (literature, compounds, citations).
2. For literature: task({ agent: research-web, task: 'search arXiv for X' }).
3. For compounds: task({ agent: research-web, task: 'search PubChem for Y' }).
4. Each sub-task MUST call save-findings to persist results.
5. Collect: load-findings to read all results.
6. Compile and call research-save to save final report.

Rules: include DOIs and CIDs, verify across 2+ sources, never invent data.
