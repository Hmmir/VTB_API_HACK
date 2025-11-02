---
description: Identify underspecified areas in the current feature spec by asking up to 5 highly targeted clarification questions and encoding answers back into the spec.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

Goal: Detect and reduce ambiguity or missing decision points in the active feature specification and record the clarifications directly in the spec file.

Note: This clarification workflow is expected to run (and be completed) BEFORE invoking `/speckit.plan`. If the user explicitly states they are skipping clarification (e.g., exploratory spike), you may proceed, but must warn that downstream rework risk increases.

Execution steps:

1. Run `.specify/scripts/powershell/check-prerequisites.ps1 -Json -PathsOnly` from repo root **once**. Parse minimal JSON payload fields:
   - `FEATURE_DIR`
   - `FEATURE_SPEC`
   - If JSON parsing fails, abort and instruct user to re-run `/speckit.specify` or verify feature branch environment.

2. Load the current spec file. Perform a structured ambiguity & coverage scan.

3. Generate (internally) a prioritized queue of candidate clarification questions (maximum 5).
    - Maximum of 5 total questions across the whole session.
    - Each question must be answerable with EITHER:
       - A short multiple‑choice selection (2–5 distinct, mutually exclusive options), OR
       - A one-word / short‑phrase answer (explicitly constrain: "Answer in <=5 words").
    - Only include questions whose answers materially impact architecture, data modeling, task decomposition, test design, UX behavior, operational readiness, or compliance validation.

4. Sequential questioning loop (interactive):
    - Present EXACTLY ONE question at a time.
    - For multiple‑choice questions:
       - **Analyze all options** and determine the **most suitable option**
       - Present your **recommended option prominently** at the top with clear reasoning
       - Format as: `**Recommended:** Option [X] - <reasoning>`
       - Then render all options as a Markdown table
    - After the user answers, record it and move to the next queued question.
    - Stop when all critical ambiguities resolved or you reach 5 questions.

5. Integration after EACH accepted answer (incremental update approach):
    - Maintain in-memory representation of the spec
    - Ensure a `## Clarifications` section exists
    - Under it, create a `### Session YYYY-MM-DD` subheading for today
    - Append: `- Q: <question> → A: <final answer>`
    - Apply the clarification to the most appropriate section(s)
    - Save the spec file AFTER each integration

6. Validation (performed after EACH write plus final pass):
   - Clarifications session contains exactly one bullet per accepted answer
   - Total asked questions ≤ 5
   - No contradictory earlier statement remains
   - Markdown structure valid

7. Write the updated spec back to `FEATURE_SPEC`.

8. Report completion:
   - Number of questions asked & answered
   - Path to updated spec
   - Sections touched
   - Coverage summary
   - Suggested next command

Behavior rules:

- If no meaningful ambiguities found, respond: "No critical ambiguities detected worth formal clarification." and suggest proceeding.
- Never exceed 5 total asked questions
- Avoid speculative tech stack questions unless the absence blocks functional clarity
- Respect user early termination signals ("stop", "done", "proceed")

