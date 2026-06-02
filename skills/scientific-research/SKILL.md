---
name: scientific-research
description: Scientific research: papers, compounds, citations, resources. Uses arXiv, PubChem, Crossref, web-search. Saves report to file.
---
# Scientific Research

Divide research into independent sub-tasks. Delegate each with task to save tokens.

## Protocol

1. **SCOPING** — Define domain, key terms, research questions
2. **LITERATURE SEARCH** — arXiv for papers, PubChem for compounds, Crossref for citations
3. **WEB CONTEXT** — web-search_full-web-search for supplementary info and context
4. **DEEP DETAILS** — Extract DOIs, CIDs, key findings, methodologies
5. **VERIFY** — Cross-check across 2+ independent sources
6. **SAVE REPORT** — Call research-save to persist final report to ./research/

## Task Delegation

For large research, delegate sub-tasks:
- Literature: `task({ agent: research-web, task: 'search arXiv for X' })`
- Compounds: `task({ agent: research-web, task: 'search PubChem for Y' })`
- Web context: `task({ agent: research-web, task: 'find supplementary info on Z' })`

Each sub-task MUST call save-findings to persist results.

## Tools Available

- arxiv: papers and preprints
- pubchem: chemical compounds and data
- web-search: supplementary information
- pdf: read research papers
- playwright: access web resources
- memory: store key findings

## Rules

- This is RESEARCH not code — do NOT use git/grep/code tools
- Include DOIs and CIDs wherever possible
- Verify across 2+ independent sources
- Never invent data or citations
- Always save final report with research-save
