---
description: Perform a non-destructive cross-artifact consistency and quality analysis across spec.md, plan.md, and tasks.md after task generation.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Identify inconsistencies, duplications, ambiguities, and underspecified items across the three core artifacts (`spec.md`, `plan.md`, `tasks.md`) before implementation. This command MUST run only after `/speckit.tasks` has successfully produced a complete `tasks.md`.

## Operating Constraints

**STRICTLY READ-ONLY**: Do **not** modify any files. Output a structured analysis report. Offer an optional remediation plan (user must explicitly approve before any follow-up editing commands would be invoked manually).

**Constitution Authority**: The project constitution (`memory/constitution.md`) is **non-negotiable** within this analysis scope. Constitution conflicts are automatically CRITICAL and require adjustment of the spec, plan, or tasks.

## Execution Steps

### 1. Initialize Analysis Context

Run `.specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks` once from repo root and parse JSON for FEATURE_DIR and AVAILABLE_DOCS. Derive absolute paths:

- SPEC = FEATURE_DIR/spec.md
- PLAN = FEATURE_DIR/plan.md
- TASKS = FEATURE_DIR/tasks.md

Abort with an error message if any required file is missing.

### 2. Load Artifacts (Progressive Disclosure)

Load only the minimal necessary context from each artifact.

### 3. Build Semantic Models

Create internal representations:

- **Requirements inventory**: Each functional + non-functional requirement
- **User story/action inventory**: Discrete user actions with acceptance criteria
- **Task coverage mapping**: Map each task to one or more requirements or stories
- **Constitution rule set**: Extract principle names and MUST/SHOULD normative statements

### 4. Detection Passes

Focus on high-signal findings. Limit to 50 findings total.

#### A. Duplication Detection
- Identify near-duplicate requirements

#### B. Ambiguity Detection
- Flag vague adjectives lacking measurable criteria
- Flag unresolved placeholders (TODO, etc.)

#### C. Underspecification
- Requirements missing measurable outcomes
- Tasks referencing undefined components

#### D. Constitution Alignment
- Any requirement conflicting with a MUST principle
- Missing mandated sections

#### E. Coverage Gaps
- Requirements with zero associated tasks
- Tasks with no mapped requirement/story

#### F. Inconsistency
- Terminology drift
- Conflicting requirements

### 5. Severity Assignment

- **CRITICAL**: Violates constitution MUST, missing core artifact, or zero coverage
- **HIGH**: Duplicate/conflicting requirement, ambiguous security/performance
- **MEDIUM**: Terminology drift, missing non-functional task coverage
- **LOW**: Style/wording improvements

### 6. Produce Compact Analysis Report

Output a Markdown report with:

- Findings table (ID, Category, Severity, Location, Summary, Recommendation)
- Coverage Summary Table
- Constitution Alignment Issues
- Unmapped Tasks
- Metrics (Total Requirements, Total Tasks, Coverage %, Issue Counts)

### 7. Provide Next Actions

- If CRITICAL issues exist: Recommend resolving before `/speckit.implement`
- If only LOW/MEDIUM: User may proceed with suggestions

### 8. Offer Remediation

Ask: "Would you like me to suggest concrete remediation edits for the top N issues?"

## Operating Principles

- **NEVER modify files** (this is read-only analysis)
- **NEVER hallucinate missing sections**
- **Prioritize constitution violations** (always CRITICAL)
- **Use examples over exhaustive rules**
- **Report zero issues gracefully**

