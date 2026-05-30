# Rebert — runnable prototypes

Shared library: `rebert/classes/`  
API key setup: `rebert/tools/register_rec_server_key.py`

## Prototypes in this repo

| Folder | Launch | Notes |
|--------|--------|-------|
| `_prototype_2_/` | `python recommender_2.0.py` | Early prototype |
| `_prototype_3_/` | `python recommender_3.0.py` | |
| `_prototype_4_/` | `python recommender_4.0.py` | |
| `_prototype_5_/` | `python recommender_5.0.py` | Review collection + main UI |
| `_prototype_6_/` | `python recommender_6.0.py` | Ephemeral recommendations |
| `_prototype_7_/` | `python recommender_7.0.py` | Ratings + audio |
| `_prototype_7_1_/` | `python recommender_7.1.py` | **Course base app (p7.1)** |

## Quick start (any prototype)

From repo root:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=.

./rebert/run.sh 7.1          # default port 5000
./rebert/run.sh 5.0 5002     # custom port
```

Each prototype expects API keys via `KeyManager` (OpenAI, TMDB, Flask secret). See root `README.md`.

## Course modification (one sub-project)

The HCDE 563 **grounded explanations** work lives in:

- **Code changes:** `rebert/_prototype_7_1_/web/` (`explanations.py`, prompts, UI)
- **Docs & study:** [`../projects/grounded-explanations/`](../projects/grounded-explanations/)

Toggle baseline vs modified with `REBERT_EXPLANATION_MODE` when running p7.1 — see that folder's README.
