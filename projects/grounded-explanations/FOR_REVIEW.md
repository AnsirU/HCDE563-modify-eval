# For Instructor Review

**Repo layout:** Full Rebert code is in [`rebert/`](../../rebert/). This folder is the HCDE 563 **course sub-project** (docs + study).

| Document | Purpose |
|----------|---------|
| [`docs/PROPOSAL.md`](docs/PROPOSAL.md) | Problem, modifications, evaluation plan |
| [`docs/IMPLEMENTATION.md`](docs/IMPLEMENTATION.md) | Code map (changes under `rebert/_prototype_7_1_/web/`) |
| [`docs/VERIFICATION.md`](docs/VERIFICATION.md) | Automated + smoke-test log |
| [`study/evaluation_protocol.md`](study/evaluation_protocol.md) | Full study procedure |
| [`study/questionnaire.md`](study/questionnaire.md) | Likert + debrief |
| [`study/scenarios.md`](study/scenarios.md) | Task scenarios |
| [`study/results/TEMPLATE_participant_scores.md`](study/results/TEMPLATE_participant_scores.md) | Scoresheet template |

## Run

```bash
# From repo root
./projects/grounded-explanations/scripts/run_baseline.sh
./projects/grounded-explanations/scripts/run_modified.sh
./rebert/run.sh 7.1
```

## Code touched by this project

All under `rebert/_prototype_7_1_/web/`:

- `explanations.py` — parse structured LLM explanations
- `prompts.py`, `llm.py`, `serve_ephem_rec.py`
- `templates/mainpage.html`, `static/rebert_mainpage_ui.js`

**Author:** Zhian Hu · **Course:** HCDE 563
