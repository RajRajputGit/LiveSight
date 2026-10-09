# AI Coding Agent Workflow

## Purpose
Use an AI coding agent as an implementation assistant while keeping architecture, correctness, and learning under your control.

## Core rule
Do not ask the agent to build the entire application in one prompt. Give it one bounded task with explicit files, constraints, acceptance criteria, and tests.

## Before each task
1. Read the relevant PRD and architecture sections.
2. Check current repository structure and Git status.
3. Define the smallest change that proves the next requirement.
4. Ask the agent to inspect existing code before editing.
5. Ask for a short plan before implementation if the change spans multiple modules.

## Task prompt template
```text
You are working on the Real-Time AI Object Detection and Monitoring System.

Read these documents before changing code:
- docs/01_PRODUCT_REQUIREMENTS.md
- docs/02_SYSTEM_ARCHITECTURE.md
- docs/03_WORKFLOW_AND_DATA_CONTRACTS.md
- [other relevant docs]

Task:
[One narrowly scoped task]

Context:
[Current behavior and relevant files]

Constraints:
- Do not implement unrelated features.
- Preserve the documented module boundaries.
- Do not move expensive inference into HTTP request handlers.
- Keep business rules deterministic and unit-testable.
- Do not invent performance claims.
- Do not add dependencies unless necessary; explain why if one is required.
- Do not overwrite unrelated user changes.
- Follow existing code style and naming.

Acceptance criteria:
- [ ] ...
- [ ] ...
- [ ] ...

Tests:
- Add/update tests for the changed behavior.
- Run relevant tests and report exact results.
- If tests cannot run, explain the blocker instead of claiming they passed.

Deliverables:
1. Code changes.
2. Tests.
3. Documentation updates if contracts or behavior changed.
4. Brief explanation of design choices and limitations.
5. Commands I can run to verify the change manually.
```

## Recommended iteration loop
### Plan
Ask the agent to inspect and propose a minimal plan. Do not allow edits yet for large tasks.

### Implement
Approve a single task. Review the diff before accepting it.

### Verify
Run tests and manually exercise the feature. Ask the agent to diagnose failures from actual output, not assumptions.

### Learn
Ask:
- Which files changed and why?
- What data enters and leaves each function?
- What alternatives were considered?
- What are the likely failure modes?
- How would I explain this design in an interview?

### Document
Update API contracts, architecture, test cases, changelog, and ADRs when relevant.

### Commit
Commit one coherent unit of work. Avoid mixing refactoring, new features, and unrelated fixes.

## Definition of done
A task is done only when:
- Its acceptance criteria are met.
- Relevant tests pass.
- The implementation matches documented contracts.
- Errors are handled intentionally.
- Documentation is updated.
- You can explain the code path without relying on the agent.

## Agent review checklist
- Did it create unnecessary abstractions?
- Did it add dependencies without a clear need?
- Did it put inference in a request handler?
- Did it hide errors or silently swallow exceptions?
- Did it invent measured FPS/accuracy results?
- Are timestamps timezone-aware?
- Are track IDs treated as temporary tracking identities?
- Are tests deterministic?
- Does it handle resource cleanup?
- Does it expose services or files unintentionally?
- Does the code work with the current project layout?

## When a bug occurs
Provide the exact command, full traceback/logs, expected behavior, actual behavior, relevant code, and reproduction steps. Ask for a diagnosis first; avoid asking the agent to rewrite the entire project.
