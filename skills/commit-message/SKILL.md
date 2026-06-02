---
name: commit-message
description: Generates clean, conventional commit messages from staged git diffs. Use when writing git commits.
---
# Commit Message Generator

## Instructions

1. Run `git diff --staged` to see all changes
2. Analyze the changes and generate a commit message

## Commit Format

```
<type>(<scope>): <short summary>

<detailed description>

<breaking changes if any>
```

## Types

- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code restructuring without behavior change
- `docs`: Documentation only
- `test`: Adding or updating tests
- `chore`: Build, CI, dependencies
- `perf`: Performance improvement
- `style`: Formatting, no logic change

## Rules

- Use present tense ("add feature" not "added feature")
- Explain what and why, not how
- Keep subject line under 72 characters
- Reference issue numbers at the end (e.g., #123)
- Separate subject from body with blank line

## Examples

```
feat(auth): add JWT token refresh mechanism

Implement automatic token refresh when access token expires.
Uses refresh token stored in httpOnly cookie.

Closes #456
```

```
fix(api): handle null response from external service

The weather API sometimes returns null for invalid locations.
Added null check and fallback to default values.

Fixes #789
```
