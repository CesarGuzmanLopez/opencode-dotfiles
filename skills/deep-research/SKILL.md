---
name: deep-research
description: Deep iterative research: ALL tools, multi-round research loop, saves comprehensive report with PDFs, docs, and complex files.
---

# Deep Research Protocol

You MUST complete ALL 5 rounds. Call research-save in round 5. FAILURE TO SAVE = TASK FAILED.

## Folder Structure

Create a comprehensive research folder for each deep research task:

```
./research/<topic>/
├── report.md              # Main comprehensive report (2000+ words)
├── sources/
│   ├── paper-1.pdf        # Downloaded papers
│   ├── paper-2.pdf
│   └── ...
├── docs/
│   ├── api-reference.md   # API documentation
│   ├── code-examples.md   # Code examples and snippets
│   ├── architecture.md    # System architecture docs
│   └── ...
├── data/
│   ├── benchmarks.csv     # Benchmark data
│   ├── comparisons.md     # Feature comparisons
│   └── ...
├── findings/
│   ├── round-1.md
│   ├── round-2.md
│   ├── round-3.md
│   ├── round-4.md
│   └── round-5.md
└── index.md               # Research index with links
```

ROUND 1 — SCOUT:
1. Call sequentialthinking to break question into 3-5 sub-topics.
2. Search each sub-topic with web-search_full-web-search (multi-engine: Bing/DuckDuckGo).
3. Use web-search_get-single-web-page-content to read detailed results.
4. **Download any PDFs found** using arxiv_download_paper or direct download.
5. **Extract and save documentation** from official sources.
6. List what you found and what gaps remain.
7. Call save-findings with filename="round-1" to persist findings.
8. DO NOT proceed without listing gaps.

ROUND 2 — DIVE:
1. Load findings from round 1 with load-findings.
2. Pick 3-5 most promising results.
3. Use web-search_get-single-web-page-content for deep page extraction.
4. Use playwright_browser_navigate if page needs JavaScript rendering.
5. **Download ALL relevant PDFs** — papers, documentation, whitepapers.
6. **Save code examples** in docs/code-examples.md with syntax highlighting.
7. **Create architecture diagrams** in docs/architecture.md.
8. Identify what's still missing.
9. Call save-findings with filename="round-2".

ROUND 3 — ITERATE:
1. Load previous findings.
2. Generate 2-3 new search queries from gaps.
3. Search again with web-search_full-web-search.
4. For scientific papers: arxiv_search_papers or pubchem_search_compounds.
5. **Download additional papers** found in this round.
6. **Extract and save API documentation** with proper formatting.
7. Store key facts with memory_add_observations.
8. Call save-findings with filename="round-3".
9. Assess convergence. If no new info → proceed to verify.

ROUND 4 — VERIFY:
1. Load all previous findings.
2. Each claim needs 2+ independent sources.
3. Check dates — prefer 2025-2026.
4. Flag contradictions explicitly.
5. **Verify all downloaded PDFs are valid** and readable.
6. **Cross-reference documentation** with actual code/examples.
7. Call save-findings with filename="round-4".

ROUND 5 — FINALIZE:
1. Load all previous findings.
2. **Compile comprehensive report** (2000+ words) with:
   - Executive summary
   - Detailed analysis per topic
   - Code examples with syntax highlighting
   - Architecture diagrams (text-based)
   - Benchmark data and comparisons
   - Recommendations with pros/cons
   - Future considerations
3. **Create index.md** linking to all resources.
4. YOU MUST CALL research-save.
5. Report saved to ./research/<topic>/<date>-report.md.
6. CONFIRM save appears. If not, retry.

RULES:
- SAVE EVERYTHING. Never trust context memory.
- **Download PDFs** — don't just reference them, actually save them.
- **Extract documentation** — save actual content, not just links.
- **Create complex files** — benchmarks, comparisons, architecture docs.
- Never finish without research-save.
- Use save-findings for each round, each finding.
- Load only what you need with load-findings.
- Always include summary for the index.
- If task fails, retry once. If still fails, document and continue.
- Use sequentialthinking before each round.
