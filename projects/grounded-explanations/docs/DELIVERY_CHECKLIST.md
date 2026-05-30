# Instructor Setup & Delivery Checklist

Use this before grading or demoing the project.

## What is in the repo (complete)

| Item | Location | Status |
|------|----------|--------|
| Runnable Rebert p4–p7.1 | `rebert/_prototype_*` | In repo |
| Shared library | `rebert/classes/` | In repo |
| Explanation implementation | `rebert/_prototype_7_1_/web/` | In repo |
| Course docs (proposal, code map) | `projects/grounded-explanations/docs/` | In repo |
| Study protocol & questionnaire | `projects/grounded-explanations/study/` | In repo |
| Automated verification log | `docs/VERIFICATION.md` | In repo |
| Example explanation output | `study/results/example_structured_explanation.json` | In repo |
| Launch scripts | `rebert/run.sh`, `projects/.../scripts/` | In repo |

## What the instructor must provide locally (not in git)

1. **Python 3.9+** and `pip install -r requirements.txt`
2. **API keys** via KeyManager (`~/.apikey_manager/access_keys.json` or course-equivalent path):
   - OpenAI — domain `api.openai.com`
   - TMDB — domain `api.themoviedb.org`
   - Flask secret — username `rebert.server0`, domain `recs.rebert.net`  
     Register: `PYTHONPATH=. python rebert/tools/register_rec_server_key.py '<secret>'`
3. **`export PYTHONPATH=.`** from repo root before running

## Quick demo path (~5 min)

```bash
git clone https://github.com/AnsirU/hcde563-rebert-explanations.git
cd hcde563-rebert-explanations
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=.

# No OpenAI needed:
python projects/grounded-explanations/scripts/verify_project.py

# With keys configured:
./projects/grounded-explanations/scripts/run_modified.sh   # :5001
# → Answer 3 questions → Recommend → see "Why this title" panel
./projects/grounded-explanations/scripts/run_baseline.sh   # :5000 for comparison
```

**Note:** First run on a new calendar day may take **several minutes** while Rebert collects movie/review data into `web/tmp/` (gitignored). Subsequent same-day launches are fast.

## Showing implementation + results

| To show… | Open… |
|----------|--------|
| Proposal & plan | `projects/grounded-explanations/docs/PROPOSAL.md` |
| Code ↔ design mapping | `docs/IMPLEMENTATION.md` |
| Technical verification | `docs/VERIFICATION.md` |
| Example structured explanation (JSON) | `study/results/example_structured_explanation.json` |
| Live UI (modified) | Run modified script → complete Q&A → Recommend |
| Participant scores (when available) | Fill `study/results/TEMPLATE_participant_scores.md` |

## Known gaps (honest status)

- **User study scores (P1–P5):** template only — fill in after running participants.
- **UI screenshots:** not included; capture after running modified condition.
- **Prototype 2.0 / 3.0:** CLI explore scripts only; web demos use p5.0+.

## Student confirmation (Zhian Hu)

- [x] Level 1 prompt + parsing implemented  
- [x] Level 2 UI panel + Q&A link implemented  
- [x] Level 3 optional via `modified_full`  
- [x] Baseline/modified toggle for within-subjects study  
- [x] Full Rebert codebase pushed; explanation is one sub-project folder  
