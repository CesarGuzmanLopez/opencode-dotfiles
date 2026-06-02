---
name: deep-research
description: Deep iterative research: ALL tools, multi-round research loop, saves comprehensive report.
---
You MUST complete ALL 5 rounds. Call research-save in round 5. FAILURE TO SAVE = TASK FAILED.

ROUND 1 — SCOUT:
1. Call sequentialthinking to break question into 3-5 sub-topics.
2. Search each sub-topic with web-search_full-web-search (multi-engine: Bing/DuckDuckGo).
3. Use web-search_get-single-web-page-content to read detailed results.
4. List what you found and what gaps remain.
5. Call save-findings with filename="round-1" to persist findings.
6. DO NOT proceed without listing gaps.

ROUND 2 — DIVE:
1. Load findings from round 1 with load-findings.
2. Pick 3-5 most promising results.
3. Use web-search_get-single-web-page-content for deep page extraction.
4. Use playwright_browser_navigate if page needs JavaScript rendering.
5. Use read_pdf if there are PDF papers.
6. Identify what's still missing.
7. Call save-findings with filename="round-2".

ROUND 3 — ITERATE:
1. Load previous findings.
2. Generate 2-3 new search queries from gaps.
3. Search again with web-search_full-web-search.
4. For scientific papers: arxiv_search_papers or pubchem_search_compounds.
5. Store key facts with memory_add_observations.
6. Call save-findings with filename="round-3".
7. Assess convergence. If no new info → proceed to verify.

ROUND 4 — VERIFY:
1. Load all previous findings.
2. Each claim needs 2+ independent sources.
3. Check dates — prefer 2025-2026.
4. Flag contradictions explicitly.
5. Call save-findings with filename="round-4".

ROUND 5 — FINALIZE:
1. Load all previous findings.
2. Compile into structured report.
3. YOU MUST CALL research-save.
4. Report saved to ./research/<topic>/<date>-report.md.
5. CONFIRM save appears. If not, retry.

RULES:
- SAVE EVERYTHING. Never trust context memory.
- Never finish without research-save.
- Use save-findings for each round, each finding.
- Load only what you need with load-findings.
- Always include summary for the index.
- If task fails, retry once. If still fails, document and continue.
- Use sequentialthinking before each round.
