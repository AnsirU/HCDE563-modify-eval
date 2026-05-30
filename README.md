# Grounded Explanations for Rebert (HCDE 563)

Course project extending **Rebert Prototype 7.1** with structured, user-linked recommendation explanations for a within-subjects evaluation of transparency, trust, and control.

**Author:** Zhian Hu  
**Course:** HCDE 563  
**Base prototype:** Rebert p7.1

## What changed

| Level | Description | Key files |
|-------|-------------|-----------|
| **Level 1** | LLM outputs structured explanation tags (`USER_ALIGNMENT`, `REVIEW_BASIS`, `CONFIDENCE`) alongside match/rationale | `web/prompts.py`, `web/llm.py`, `web/explanations.py` |
| **Level 2** | Compact **Why this title** panel with bullets; click a user-alignment bullet to highlight the linked Q&A answer | `web/templates/mainpage.html`, `web/static/rebert_mainpage_ui.js` |
| **Level 3 (optional)** | Trimmed review excerpts with IDs (`R1`, `R2`, …) passed into the LLM | `web/explanations.py`, env `REBERT_EXPLANATION_MODE=modified_full` |

Baseline (original p7.1 recommendation UI) and modified versions run from the **same codebase** via an environment variable — suitable for counterbalanced A/B sessions.

## Repository layout

```
HCDE563/
├── FOR_REVIEW.md                      # start here (instructor index)
├── README.md                          # setup & run instructions
├── docs/
│   ├── PROPOSAL.md                    # course proposal summary
│   ├── IMPLEMENTATION.md              # code ↔ proposal mapping
│   └── VERIFICATION.md                # test log (modify + baseline smoke)
├── study/                             # evaluation protocol & instruments
│   ├── evaluation_protocol.md
│   ├── scenarios.md
│   └── questionnaire.md
└── rebert/
    ├── _prototype_7_1_/               # modified Rebert p7.1 + explanations
    │   ├── recommender_7.1.py
    │   └── web/
    │       ├── explanations.py        # parse/format structured explanations
    │       ├── prompts.py
    │       ├── llm.py
    │       ├── serve_ephem_rec.py
    │       └── templates/mainpage.html
    ├── classes/                       # shared Rebert library
    └── tools/register_rec_server_key.py
```

## Prerequisites

1. **Python 3.9+**
2. **API keys** registered with Rebert's `KeyManager`:
   - OpenAI (`api.openai.com`)
   - TMDB (`api.themoviedb.org`)
   - Flask session secret (`recs.rebert.net`)

```bash
cd /path/to/HCDE563
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Register Flask secret (once)
PYTHONPATH=. python3 rebert/tools/register_rec_server_key.py 'your-long-random-secret'
```

Add OpenAI and TMDB keys using the same KeyManager workflow your course materials describe.

## Run the server

From the repo root:

```bash
source .venv/bin/activate
export PYTHONPATH=.
cd rebert/_prototype_7_1_
```

### Modified condition (default)

Structured explanations enabled:

```bash
export REBERT_EXPLANATION_MODE=modified
python recommender_7.1.py -port 5001
```

Or use the helper script from repo root:

```bash
./scripts/run_modified.sh
```

Open http://127.0.0.1:5001

### Baseline condition

Original p7.1 recommendation presentation (no Why panel):

```bash
export REBERT_EXPLANATION_MODE=baseline
python recommender_7.1.py -port 5000
```

Or:

```bash
./scripts/run_baseline.sh
```

Open http://127.0.0.1:5000

### Level 3 (optional)

Review excerpt IDs in the LLM prompt:

```bash
export REBERT_EXPLANATION_MODE=modified_full
python recommender_7.1.py -port 5001
```

## Study workflow

1. Counterbalance order: half of participants **Baseline → Modified**, half **Modified → Baseline**.
2. Use **different scenarios** per condition (see `study/scenarios.md`).
3. After each condition, administer the post-task survey (`study/questionnaire.md`).
4. End with comparative questions and a short debrief.

Full procedure: `study/evaluation_protocol.md`

## Evaluation success criteria (from proposal)

- ≥3/5 participants improve on **Transparency**
- ≥3/5 participants improve on **Trust**
- Modified chosen more often on the “more honest about AI limits” question
- No strong negative pattern on cognitive load

## Development notes

- First launch may take several minutes while movie/review data is collected; subsequent same-day launches reuse cached data in `web/tmp/`.
- The study banner at the top of the page shows which condition is active.
- Explanation parsing lives in `web/explanations.py` for easy unit testing without calling the LLM.

## License / attribution

Built on Rebert prototypes by David W. McDonald (University of Washington). Course modifications by Zhian Hu for HCDE 563.
