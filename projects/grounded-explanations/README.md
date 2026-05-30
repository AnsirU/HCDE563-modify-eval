# Grounded Explanations (HCDE 563 sub-project)

This folder is the **course project** layered on top of Rebert p7.1.  
The runnable app is **`rebert/_prototype_7_1_/`** (shared with the rest of the repo).

**Author:** Zhian Hu · **Course:** HCDE 563

## What's here vs in `rebert/`

| Location | Contents |
|----------|----------|
| `rebert/_prototype_7_1_/` | Full Flask app + **explanation code** (`web/explanations.py`, UI, prompts) |
| `projects/grounded-explanations/` (here) | Proposal, implementation notes, study protocol, run scripts |

## Run conditions (baseline vs modified)

From repo root:

```bash
./projects/grounded-explanations/scripts/run_baseline.sh    # port 5000
./projects/grounded-explanations/scripts/run_modified.sh    # port 5001
```

Or via generic launcher:

```bash
REBERT_EXPLANATION_MODE=baseline ./rebert/run.sh 7.1 5000
REBERT_EXPLANATION_MODE=modified ./rebert/run.sh 7.1 5001
```

| Mode | Env var | UI |
|------|---------|-----|
| Baseline | `REBERT_EXPLANATION_MODE=baseline` | Original p7.1 |
| Modified | `REBERT_EXPLANATION_MODE=modified` | “Why this title” panel |
| Level 3 | `REBERT_EXPLANATION_MODE=modified_full` | Modified + review excerpt IDs |

## Instructor review

Start at [`FOR_REVIEW.md`](FOR_REVIEW.md).

## Verify (no OpenAI)

```bash
PYTHONPATH=. python projects/grounded-explanations/scripts/verify_project.py
```

## Implementation summary

| Level | Files under `rebert/_prototype_7_1_/web/` |
|-------|-------------------------------------------|
| 1 | `prompts.py`, `llm.py`, `explanations.py` |
| 2 | `templates/mainpage.html`, `static/rebert_mainpage_ui.js` |
| 3 | `explanations.py` (excerpt IDs), env `modified_full` |

See [`docs/IMPLEMENTATION.md`](docs/IMPLEMENTATION.md).
