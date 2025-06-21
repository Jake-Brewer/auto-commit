# LLM Guide to Writing Quality Commit Messages
# Last Updated: 2025-06-19T10:00:00Z

## Introduction

A well-crafted Git commit message is the best way to communicate context about a change to fellow developers and your future self. A diff will tell you *what* changed, but only the commit message can properly tell you *why*. A well-cared-for log is a beautiful and useful thing.

This guide outlines the best practices for writing commit messages, including the widely adopted Conventional Commits standard.

## The Seven Rules of a Great Git Commit Message

These rules are based on established community standards and help ensure your commit history is clean, readable, and useful.

1.  **Separate subject from body with a blank line.**
    - The first line is the subject (or summary).
    - The rest of the text is the body.
    - Tools like `git log --oneline` and GitHub's UI rely on this separation.

2.  **Limit the subject line to 50 characters.**
    - Keeps messages readable and concise.
    - GitHub's UI truncates long subject lines.

3.  **Capitalize the subject line.**
    - "Add new feature" not "add new feature".

4.  **Do not end the subject line with a period.**
    - "Update documentation for API" not "Update documentation for API."

5.  **Use the imperative mood in the subject line.**
    - Write as if you are giving a command.
    - Example: "Fix bug in user authentication" instead of "Fixed bug..." or "Fixes bug...".
    - A simple test: A properly formed subject line should always be able to complete the sentence: "If applied, this commit will... _[your subject line]_".

6.  **Wrap the body at 72 characters.**
    - Git does not automatically wrap text. Manual wrapping ensures readability in the terminal.

7.  **Use the body to explain *what* and *why* vs. *how*.**
    - Explain the problem the commit solves.
    - Detail the reasoning behind your solution.
    - The code itself explains *how* the change was made.

---

## Conventional Commits

The Conventional Commits specification is a convention built on top of these rules. It provides a simple, structured way to write commit messages that is both human- and machine-readable. This structure helps automate things like generating changelogs and determining semantic version bumps.

### Structure

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types

The most common types include:

- **feat**: A new feature for the user. (Correlates with `MINOR` in SemVer).
- **fix**: A bug fix for the user. (Correlates with `PATCH` in SemVer).
- **docs**: Changes to documentation only.
- **style**: Changes that do not affect the meaning of the code (white-space, formatting, etc).
- **refactor**: A code change that neither fixes a bug nor adds a feature.
- **perf**: A code change that improves performance.
- **test**: Adding missing tests or correcting existing tests.
- **build**: Changes that affect the build system or external dependencies (e.g., gulp, broccoli, npm).
- **ci**: Changes to our CI configuration files and scripts (e.g., Travis, Circle, BrowserStack, SauceLabs).
- **chore**: Other changes that don't modify `src` or `test` files.
- **revert**: Reverts a previous commit.

### Scope (Optional)

A scope provides additional contextual information and is contained within parentheses. It can be anything specifying the place of the commit change.

- `feat(parser): add ability to parse arrays`
- `fix(api): correct calculation for user totals`

### Breaking Changes

Breaking changes, which correlate with `MAJOR` in SemVer, must be indicated.

1.  Append a `!` after the type/scope: `feat(api)!: remove user endpoint`
2.  Add a `BREAKING CHANGE:` footer:
    ```
    refactor: restructure user authentication module

    BREAKING CHANGE: The `authenticate` function now returns a promise
    instead of a callback.
    ```

### Examples

**Good Commit Messages:**

- `feat: allow users to upload profile pictures`
- `fix(auth): prevent password hash from being exposed in API response`
- `docs: update installation instructions in README.md`
- `refactor!: rename primary export to createThing`
- `perf: improve rendering speed by memoizing component`

**Bad Commit Messages:**

- `fixed stuff` (unclear, not imperative, no capitalization)
- `Update` (too vague)
- `add new file and fix bug in other file` (doing too much in one commit)
- `feat: add a new really cool and awesome feature that does a lot of things` (subject too long)

## Conclusion

Writing high-quality commit messages is a skill that pays dividends. It improves team collaboration, simplifies debugging, and provides a valuable historical record of your project. By following these guidelines, you contribute to a cleaner, more maintainable codebase. 