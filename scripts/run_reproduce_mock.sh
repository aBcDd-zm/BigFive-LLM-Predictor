#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

PYTHON_BIN="${PYTHON_BIN:-python}"
if [[ -x ".venv/bin/python" ]]; then
  PYTHON_BIN=".venv/bin/python"
fi

REQUEST_DIR="outputs/bfi_requests"
REQUEST_FILE="$REQUEST_DIR/request.jsonl"
RESPONSE_FILE="outputs/response.jsonl"
OCEAN_FILE="outputs/ocean_scores.csv"
METRICS_FILE="outputs/evaluation_metrics.csv"

mkdir -p outputs "$REQUEST_DIR"
rm -f "$REQUEST_FILE" "$REQUEST_DIR/run.sh" "$RESPONSE_FILE" "$OCEAN_FILE" "$METRICS_FILE"

echo "[1/4] Generating BFI requests..."
"$PYTHON_BIN" src/generate_bfi_requests.py \
  --model_name kurileo/Gemma-2-2b-it-BFI-Anonymous \
  --source_path data/dialogues \
  --output_path "$REQUEST_DIR"

echo "[2/4] Running mock inference..."
"$PYTHON_BIN" src/run_local_inference.py \
  --backend mock \
  --requests_path "$REQUEST_FILE" \
  --output_path "$RESPONSE_FILE"

echo "[3/4] Processing OCEAN scores..."
"$PYTHON_BIN" src/process_results.py \
  --response_paths "$RESPONSE_FILE" \
  --output_path "$OCEAN_FILE"

echo "[4/4] Evaluating metrics..."
"$PYTHON_BIN" src/evaluate_ocean.py \
  --pred_path "$OCEAN_FILE" \
  --truth_path data/ground_truth.csv \
  --output_path "$METRICS_FILE"

echo "Done. Generated:"
echo "  $REQUEST_FILE"
echo "  $RESPONSE_FILE"
echo "  $OCEAN_FILE"
echo "  $METRICS_FILE"
