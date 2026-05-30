# For Instructor Review

Quick index to the HCDE 563 course project deliverables.

| Document | Purpose |
|----------|---------|
| [`docs/PROPOSAL.md`](docs/PROPOSAL.md) | Problem, modifications, evaluation plan, success criteria |
| [`docs/IMPLEMENTATION.md`](docs/IMPLEMENTATION.md) | Code map: Level 1–3, files changed, data flow |
| [`docs/VERIFICATION.md`](docs/VERIFICATION.md) | Automated + server smoke-test log (2026-05-30) |
| [`study/evaluation_protocol.md`](study/evaluation_protocol.md) | Full study procedure |
| [`study/questionnaire.md`](study/questionnaire.md) | Likert + debrief instruments |
| [`study/scenarios.md`](study/scenarios.md) | Counterbalanced task scenarios |
| [`study/results/TEMPLATE_participant_scores.md`](study/results/TEMPLATE_participant_scores.md) | Blank scoresheet for N=5 analysis |

## Run the two conditions

```bash
./scripts/run_baseline.sh    # port 5000 — original p7.1
./scripts/run_modified.sh    # port 5001 — structured explanations
```

## Verify without a live study session

```bash
PYTHONPATH=. python scripts/verify_project.py
```

## Core code (modified prototype)

- `rebert/_prototype_7_1_/web/explanations.py` — parse/format structured explanations
- `rebert/_prototype_7_1_/web/prompts.py` — LLM prompt extensions
- `rebert/_prototype_7_1_/web/llm.py` — recommendation request + parsing
- `rebert/_prototype_7_1_/web/templates/mainpage.html` — “Why this title” UI

**Author:** Zhian Hu · **Course:** HCDE 563
