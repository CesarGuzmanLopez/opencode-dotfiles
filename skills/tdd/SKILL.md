---
name: tdd
description: Test-driven development workflow. Write tests first, then implement. Use when building new features or fixing bugs.
---
# Test-Driven Development (TDD)

## The Red-Green-Refactor Cycle

```
1. RED   — Write a failing test that defines desired behavior
2. GREEN — Write minimal code to make the test pass
3. REFACTOR — Clean up code while keeping tests green
```

## Process

### Step 1: Understand Requirements
- What should the code do?
- What are the inputs and outputs?
- What are the edge cases?

### Step 2: Write Failing Tests (RED)
- Start with the simplest test case
- Test one behavior per test
- Use descriptive test names
- Run tests to confirm they fail

### Step 3: Implement Minimal Code (GREEN)
- Write just enough code to pass
- Don't optimize yet
- Don't handle edge cases yet
- Run tests to confirm they pass

### Step 4: Refactor (REFACTOR)
- Improve code structure
- Remove duplication
- Add edge case handling
- Run tests to confirm nothing broke

## Rules

- Never write production code without a failing test first
- One test at a time
- Commit after each green-refactor cycle
- Tests are documentation — make them readable

## Test Structure

```python
def test_<what>():
    # Arrange — set up test data
    # Act — call the function
    # Assert — verify the result
```

## What to Test

- Happy path (expected behavior)
- Edge cases (boundaries, empty input, null)
- Error cases (invalid input, exceptions)
- Integration points (APIs, databases)

## Anti-Patterns to Avoid

- Testing implementation details (test behavior, not internals)
- Writing tests after code (defeats the purpose)
- Skipping the refactor step (technical debt accumulates)
- Testing too much at once (keep tests small and focused)

## When to Apply TDD

- New features with clear requirements
- Bug fixes (write test that reproduces bug first)
- Refactoring (tests ensure behavior doesn't change)
- Complex algorithms
- API endpoints

## Output

For each feature, produce:
1. Test file with failing tests
2. Implementation file
3. All tests passing
4. Refactored code
