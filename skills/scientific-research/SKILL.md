---
name: scientific-research
description: Scientific research: papers, compounds, citations, resources. Uses arXiv, PubChem, Crossref, web-search. Saves comprehensive report with PDFs to file.
---
# Scientific Research

Divide research into independent sub-tasks. Delegate each with task to save tokens.

## Folder Structure

Create a comprehensive research folder for each scientific research task:

```
./research/<topic>/
├── report.md              # Main scientific report
├── papers/
│   ├── paper-1.pdf        # Downloaded research papers
│   ├── paper-2.pdf
│   └── ...
├── compounds/
│   ├── compound-data.md   # Chemical compound data
│   └── ...
├── citations/
│   ├── references.bib     # Bibliography
│   └── ...
├── findings/
│   └── detailed-findings.md
└── index.md               # Research index with DOIs/CIDs
```

## Protocol

1. **SCOPING** — Define domain, key terms, research questions
2. **LITERATURE SEARCH** — arXiv for papers, PubChem for compounds, Crossref for citations
3. **DOWNLOAD PAPERS** — Use arxiv_download_paper to save PDFs locally
4. **WEB CONTEXT** — web-search_full-web-search for supplementary info and context
5. **EXTRACT DATA** — Save compound data, citation info, methodologies
6. **DEEP DETAILS** — Extract DOIs, CIDs, key findings, methodologies
7. **VERIFY** — Cross-check across 2+ independent sources
8. **SAVE REPORT** — Call research-save to persist final report to ./research/

## Task Delegation

For large research, delegate sub-tasks:
- Literature: `task({ agent: research-web, task: 'search arXiv for X' })`
- Compounds: `task({ agent: research-web, task: 'search PubChem for Y' })`
- Web context: `task({ agent: research-web, task: 'find supplementary info on Z' })`

Each sub-task MUST call save-findings to persist results.

## Tools Available

- arxiv: papers and preprints (download with arxiv_download_paper)
- pubchem: chemical compounds and data
- web-search: supplementary information
- pdf: read research papers
- playwright: access web resources
- memory: store key findings

## Rules

- This is RESEARCH not code — do NOT use git/grep/code tools
- **Download papers** — use arxiv_download_paper to save PDFs locally
- **Save compound data** — create structured files with CID, SMILES, properties
- Include DOIs and CIDs wherever possible
- Verify across 2+ independent sources
- Never invent data or citations
- Always save final report with research-save
