---
name: project-research-code
description: Code project research: analyzes codebase AND searches internet. Correlates both. Saves report.
---
Split into independent tasks and delegate with task.

1. task({ agent: research-web, task: 'search for best practices on X' })
2. task({ agent: read, task: 'explore project structure for Y' })
3. Each task saves results with save-findings.
4. Collect with load-findings.
5. Correlate findings and compile report.

Protocol: EXPLORE → RESEARCH → CORRELATE → REPORT.
