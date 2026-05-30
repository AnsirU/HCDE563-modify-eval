#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT/rebert/_prototype_7_1_"

export PYTHONPATH="$ROOT"
export REBERT_EXPLANATION_MODE=modified

if [[ -d "$ROOT/.venv/bin" ]]; then
  # shellcheck disable=SC1091
  source "$ROOT/.venv/bin/activate"
fi

echo "Starting Rebert p7.1 MODIFIED (grounded explanations) on http://127.0.0.1:5001"
python recommender_7.1.py -port 5001
