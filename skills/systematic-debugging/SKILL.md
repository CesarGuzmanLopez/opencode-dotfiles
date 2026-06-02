---
name: systematic-debugging
description: Methodical problem-solving for bugs and errors. Use when debugging issues or investigating failures.
---
# Systematic Debugging

## Process

1. **Reproduce** — Create minimal steps to trigger the bug
2. **Isolate** — Narrow down to the smallest possible scope
3. **Hypothesize** — Form 2-3 possible causes
4. **Test** — Verify each hypothesis with evidence
5. **Fix** — Apply the minimal fix that addresses root cause
6. **Verify** — Confirm the fix works and doesn't break other things

## Rules

- Never guess. Always verify with evidence.
- Start from what you know, not what you think.
- Change one thing at a time.
- Document each step and finding.
- Check the simplest explanation first.

## Common Debugging Patterns

### Code not executing
- Check if the code path is actually reached (add log/print)
- Verify imports and module loading
- Check for syntax errors that prevent loading

### Wrong output
- Trace data flow from input to output
- Check intermediate values at each step
- Verify assumptions about data types and formats

### Performance issues
- Profile before optimizing
- Check for N+1 queries, unnecessary loops, missing indexes
- Measure actual vs expected complexity

### Intermittent failures
- Check for race conditions, shared state, timing issues
- Look at logs for patterns (time of day, load, etc.)
- Check external dependencies (APIs, databases, networks)

## Output Format

When debugging, always output:
1. What you observed
2. What you expected
3. Steps to reproduce
4. Hypotheses tested
5. Root cause found
6. Fix applied
7. Verification results
