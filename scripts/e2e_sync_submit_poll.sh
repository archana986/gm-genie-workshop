#!/usr/bin/env bash
# Sync all GM-Genie-Workshop artifacts, submit serverless E2E job (--no-wait), poll until SUCCESS or FAILURE.
# No prompts. Set PROFILE / WORKSPACE_PATH / CURSOR_ROOT if needed.
#
# Usage (from anywhere):
#   bash Customer-Work/GM-Genie-Workshop/scripts/e2e_sync_submit_poll.sh
#
# Or from GM-Genie-Workshop:
#   bash scripts/e2e_sync_submit_poll.sh
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GM_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
# Default: Cursor layout Customer-Work/GM-Genie-Workshop → repo root is two levels up
CURSOR_ROOT="${CURSOR_ROOT:-$(cd "$GM_ROOT/../.." && pwd)}"
SYNC_SH="${CURSOR_ROOT}/Customer-Work/AMA-GM/sync_workspace_artifacts.sh"
JOB_JSON="${GM_ROOT}/scripts/job_submit_gm_genie_e2e_01_09.json"

PROFILE="${PROFILE:-azure-aiquery}"
WORKSPACE_PATH="${WORKSPACE_PATH:-/Workspace/Users/archana.krishnamurthy@databricks.com/GM-Genie-Workshop}"
POLL_SECS="${POLL_SECS:-90}"
MAX_ITERS="${MAX_ITERS:-200}"

if [[ ! -f "$SYNC_SH" ]]; then
  echo "ERROR: sync script not found: $SYNC_SH"
  echo "Set CURSOR_ROOT to your workspace root (folder containing Customer-Work/)."
  exit 1
fi

if [[ ! -f "$JOB_JSON" ]]; then
  echo "ERROR: job JSON not found: $JOB_JSON"
  exit 1
fi

cd "$CURSOR_ROOT"
echo "== Sync (PROFILE=$PROFILE WORKSPACE_PATH=$WORKSPACE_PATH) =="
PROFILE="$PROFILE" WORKSPACE_PATH="$WORKSPACE_PATH" "$SYNC_SH" \
  "Customer-Work/GM-Genie-Workshop/notebooks/01_setup_data.ipynb" \
  "Customer-Work/GM-Genie-Workshop/notebooks/02_create_genie_spaces.ipynb" \
  "Customer-Work/GM-Genie-Workshop/notebooks/03_genie_evals_benchmarks.ipynb" \
  "Customer-Work/GM-Genie-Workshop/notebooks/04_talk_with_data.ipynb" \
  "Customer-Work/GM-Genie-Workshop/notebooks/05_genie_code_skills.ipynb" \
  "Customer-Work/GM-Genie-Workshop/notebooks/06_compare_genie_spaces.ipynb" \
  "Customer-Work/GM-Genie-Workshop/notebooks/07_security_governance.ipynb" \
  "Customer-Work/GM-Genie-Workshop/notebooks/08_deployment_best_practices.ipynb" \
  "Customer-Work/GM-Genie-Workshop/notebooks/09_monitoring_observability.ipynb" \
  "Customer-Work/GM-Genie-Workshop/templates/manufacturing_genie_configured.json"

# App sources must land under WORKSPACE_PATH/app/ so notebook 08 can export app/app.py, etc.
echo "== Sync Databricks App bundle (WORKSPACE_PATH=$WORKSPACE_PATH/app) =="
PROFILE="$PROFILE" WORKSPACE_PATH="$WORKSPACE_PATH/app" "$SYNC_SH" \
  "Customer-Work/GM-Genie-Workshop/app/app.py" \
  "Customer-Work/GM-Genie-Workshop/app/app.yaml" \
  "Customer-Work/GM-Genie-Workshop/app/requirements.txt"

echo "== Submit E2E (no-wait) =="
OUT="$(databricks jobs submit -p "$PROFILE" --no-wait --timeout 240m --json @"$JOB_JSON" -o json)"
RUN_ID="$(python3 -c "import json,sys; print(json.loads(sys.argv[1])['run_id'])" "$OUT")"
echo "run_id=$RUN_ID"

echo "== Poll every ${POLL_SECS}s (max ${MAX_ITERS} iters) =="
for ((i = 1; i <= MAX_ITERS; i++)); do
  databricks jobs get-run -p "$PROFILE" "$RUN_ID" -o json > /tmp/gm_e2e_run.json
  LC="$(python3 -c "import json; d=json.load(open('/tmp/gm_e2e_run.json')); print(d.get('state',{}).get('life_cycle_state',''))")"
  RS="$(python3 -c "import json; d=json.load(open('/tmp/gm_e2e_run.json')); print(d.get('state',{}).get('result_state','') or '')")"
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) iter=$i lifecycle=$LC result=$RS"
  if [[ "$LC" == "TERMINATED" || "$LC" == "INTERNAL_ERROR" ]]; then
    python3 -c "import json; d=json.load(open('/tmp/gm_e2e_run.json')); print((d.get('state',{}).get('state_message') or '')[:500])"
    python3 -c "import json; d=json.load(open('/tmp/gm_e2e_run.json')); tasks=d.get('tasks',[]); [print(t.get('task_key'), t.get('state',{}).get('result_state')) for t in sorted(tasks, key=lambda x: x.get('task_key',''))]"
    if [[ "$RS" == "SUCCESS" ]]; then
      echo "E2E SUCCESS"
      exit 0
    fi
    echo "FAILED — inspect a task run with:"
    echo "  databricks jobs get-run-output -p $PROFILE <notebook_task_run_id>"
    exit 1
  fi
  sleep "$POLL_SECS"
done

echo "TIMEOUT after $MAX_ITERS polls"
exit 2
