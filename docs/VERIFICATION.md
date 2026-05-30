# Verification Log

**Date:** 2026-05-30  
**Command:** `PYTHONPATH=. python scripts/verify_project.py`

## Automated checks (modify + config modes)

| Check | Result |
|-------|--------|
| Parse structured explanation tags | PASS |
| Numbered Q&A string (Q1–Q3) | PASS |
| Review excerpt IDs (R1…) | PASS |
| `baseline` → grounded explanations OFF | PASS |
| `modified` → grounded explanations ON | PASS |
| `modified_full` → excerpt IDs ON | PASS |
| Modified prompt includes `<USER_ALIGNMENT>` | PASS |

## Server smoke tests

Movie data cache seeded from latest collection (`rebert-p7.1_data_20260519.json`) for local startup.

| Condition | Port | Banner text | `why-panel` on initial load |
|-----------|------|-------------|----------------------------|
| Modified | 5099 | “Modified — structured explanations” | 0 (panel appears after Recommend) |
| Baseline | 5098 | “Baseline — original recommendation UI” | 0 |

Homepage HTTP 200 for both conditions.

## Not run in this log (requires live session)

- Full ephemeral Q&A → LLM recommendation (needs OpenAI key + ~1–2 min)
- Participant study (`study/evaluation_protocol.md`) — use `study/results/TEMPLATE_participant_scores.md`

## Reproduce

```bash
# Automated
PYTHONPATH=. python scripts/verify_project.py

# Modified UI
./scripts/run_modified.sh

# Baseline UI
./scripts/run_baseline.sh
```

First launch on a new day may take several minutes while Rebert collects movie/review data unless a same-day cache exists in `rebert/_prototype_7_1_/web/tmp/`.
