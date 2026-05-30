# HCDE 563 — Rebert Course Repository

Full **Rebert** prototype codebase (runnable) plus the HCDE 563 course sub-project on grounded recommendation explanations.

**Author:** Zhian Hu · **Course:** HCDE 563

## Repository structure

```
HCDE563/
├── README.md                          ← you are here
├── requirements.txt
├── rebert/                            ← all runnable Rebert code
│   ├── run.sh                         ← launch any prototype (2.0–7.1)
│   ├── README.md                      ← prototype list & run commands
│   ├── classes/                       ← shared library (OpenAI, reviews, TMDB, …)
│   ├── tools/                         ← KeyManager setup
│   ├── _prototype_2_/ … _prototype_7_1_/   ← each version is self-contained
│   └── _prototype_7_1_/               ← course base app (p7.1)
├── projects/
│   └── grounded-explanations/         ← course docs + study only (one sub-folder)
│       ├── README.md
│       ├── FOR_REVIEW.md              ← instructor index
│       ├── docs/                      ← proposal, implementation, verification
│       ├── study/                     ← eval protocol, questionnaire, scenarios
│       └── scripts/                   ← baseline/modified launchers
└── .venv/                             ← local only (not in git)
```

**Important:** Explanation features are implemented **inside** `rebert/_prototype_7_1_/web/`.  
`projects/grounded-explanations/` holds documentation and study materials — not a separate app.

## Setup (once)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=.

# Flask session secret (once)
python rebert/tools/register_rec_server_key.py 'your-long-random-secret'
```

Register OpenAI and TMDB keys via `KeyManager` per course instructions.

## Run Rebert (any prototype)

```bash
./rebert/run.sh 5.0              # prototype 5.0, port 5000
./rebert/run.sh 7.1 5000         # prototype 7.1 (course base)
./rebert/run.sh 7.0 5002         # another version, custom port
```

See [`rebert/README.md`](rebert/README.md) for the full prototype table.

## Course sub-project: grounded explanations

Docs and study live in [`projects/grounded-explanations/`](projects/grounded-explanations/).

```bash
# Baseline vs modified (counterbalanced study)
./projects/grounded-explanations/scripts/run_baseline.sh   # :5000
./projects/grounded-explanations/scripts/run_modified.sh   # :5001

# Automated checks (no OpenAI)
PYTHONPATH=. python projects/grounded-explanations/scripts/verify_project.py
```

Instructors: start at [`projects/grounded-explanations/FOR_REVIEW.md`](projects/grounded-explanations/FOR_REVIEW.md).

## GitHub

https://github.com/AnsirU/hcde563-rebert-explanations

## Attribution

Rebert prototypes: David W. McDonald (University of Washington).  
Grounded explanations & study design: Zhian Hu (HCDE 563).
