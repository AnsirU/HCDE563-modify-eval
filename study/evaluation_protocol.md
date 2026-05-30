# Evaluation Protocol

**Project:** Grounded, User-Linked Explanations for AI Movie Recommendations  
**Prototype:** Rebert p7.1 (baseline vs modified)  
**Design:** Within-subjects, counterbalanced A/B  
**Target N:** ~5 participants (convenience sample)

## Session overview (~35–45 min)

| Step | Activity | Duration |
|------|----------|----------|
| 1 | Pre-session background questions | ~3 min |
| 2 | Condition A (scenario + task + survey) | ~12–15 min |
| 3 | Break | 1–2 min |
| 4 | Condition B (different scenario + task + survey) | ~12–15 min |
| 5 | Comparative questions + debrief interview | ~8–10 min |

## Conditions

| Condition | Environment variable | Default port | Script |
|-----------|---------------------|--------------|--------|
| Baseline | `REBERT_EXPLANATION_MODE=baseline` | 5000 | `./scripts/run_baseline.sh` |
| Modified | `REBERT_EXPLANATION_MODE=modified` | 5001 | `./scripts/run_modified.sh` |

Counterbalance:

- **Group 1:** Baseline first → Modified second  
- **Group 2:** Modified first → Baseline second

## Participant task (each condition)

1. Read the assigned scenario (`scenarios.md`).
2. Click **Answer up to 3 questions** and complete the ephemeral Q&A.
3. Click **Recommend** and review the suggestion(s).
4. In **Modified**, inspect the **Why this title** panel; optionally click bullets to see linked answers.
5. Click **Ask Rebert** on one movie and ask **one follow-up question**.
6. Complete the post-task questionnaire (`questionnaire.md`).

## Analysis plan

### Quantitative

For each Likert item (1–7), record per participant per condition:

- Individual scores
- Median across participants
- Per-participant delta: Modified − Baseline

Primary deltas: Transparency, Trust, Control/steerability.

Summarize:

- How many of 5 participants improved on each primary measure
- Whether median is higher in Modified
- Comparative question counts (more willing to watch / more honest)

### Qualitative

Thematic coding (2–3 passes) on debrief notes. Example themes:

- explanation felt grounded
- still felt generic / fabricated
- wanted stronger citations
- improved trust
- too long / cognitively heavy
- confusion about user input vs reviews

Label participants P1–P5.

## Success criteria

Modified is considered successful if:

- ≥3/5 improve on Transparency
- ≥3/5 improve on Trust
- Modified wins “more honest about AI limits” more often
- No strong negative pattern on cognitive load
