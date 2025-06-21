# LLM Troubleshooting Guide for Tool Failures
# Last Updated: 2025-06-21T11:45:00Z

## 1. Introduction

This document provides a standard operating procedure for AI agents when encountering persistent, seemingly illogical failures with core development tools like `git`. The primary goal is to avoid infinite loops of failing commands and to escalate the issue to the human user effectively.

## 2. The Problem: Inconsistent State

You may encounter a situation where the state of the system as reported by a tool (e.g., `git status`) appears to contradict the actions you have just taken (e.g., editing a file).

**Symptoms include:**
- A command fails repeatedly without a clear, actionable error message.
- `git status` reports "nothing to commit, working tree clean" immediately after files have been modified or staged.
- The output of different commands is contradictory (e.g., `git diff` shows no changes, but you know changes were made).

This often points to a deeper issue with the shell environment, the tool's installation, or the repository's metadata that the agent cannot directly fix.

## 3. Diagnostic and Recovery Protocol

When you suspect an inconsistent state, immediately halt your current task and follow this diagnostic protocol. **Do not retry the failing command more than once.**

### Step 1: Check Basic Status
Run `git status` to get the tool's perspective on the current state.
```
> git status
```

### Step 2: Verify Working Directory Changes
Run `git diff HEAD` to see if the tool recognizes changes between the working directory and the last commit.
```
> git diff HEAD
```

### Step 3: Verify the Last Commit
Run `git log -1 --stat` to confirm what was included in the most recent commit. This helps verify if a previous command succeeded unexpectedly.
```
> git log -1 --stat
```

### Step 4: Analysis and Escalation
- **If the outputs are contradictory or do not reflect reality**: You have confirmed an inconsistent state.
- **Action**:
    1.  **Do not attempt further commits or modifications.**
    2.  Clearly state the observed contradiction to the user (e.g., "I edited file X, but `git status` and `git diff` show no changes.").
    3.  Report that you are unable to complete the task due to this environmental issue.
    4.  Recommend that the user manually inspect the repository state.
    5.  Await further instructions from the user.

By following this protocol, you avoid destructive loops and provide the user with a clear, concise report of the problem, allowing them to resolve the underlying environmental issue. 