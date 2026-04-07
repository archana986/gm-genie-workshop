#!/usr/bin/env bash
# Sync manufacturing Genie workshop artifacts, submit serverless E2E job (--no-wait), poll until SUCCESS or FAILURE.
# No prompts. Set PROFILE / WORKSPACE_PATH / CURSOR_ROOT if needed.
#
# Usage (from anywhere with CURSOR_ROOT set to workspace containing Customer-Work/):
#   bash path/to/scripts/e2e_sync_submit_poll.sh
#
# Or from this repository root:
#   bash scripts/e2e_sync_submit_poll.sh
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
# Parent tree root used to locate the workspace sync helper (override with SYNC_SH).
CURSOR_ROOT="${CURSOR_ROOT:-$(cd "$REPO_ROOT/../.." && pwd)}"
SYNC_SH="${SYNC_SH:-}"
if [[ -z "$SYNC_SH" ]]; then
  SYNC_SH="$(find "$CURSOR_ROOT" -maxdepth 8 -name sync_workspace_artifacts.sh -type f 2>/dev/null | head -1 || true)"
fi
JOB_JSON="${REPO_ROOT}/scripts/job_submit_manufacturing_genie_e2e_01_09.json"

# Override PROFILE and WORKSPACE_PATH for your workspace (not used for zip-only customer runs).
PROFILE="${PROFILE:-DEFAULT}"
WORKSPACE_PATH="${WORKSPACE_PATH:-/Workspace/Shared/manufacturing-genie-workshop}"
POLL_SECS="${POLL_SECS:-90}"
MAX_ITERS="${MAX_ITERS:-200}"
E2E_RUN_JSON="${TMPDIR:-/tmp}/mfg_genie_e2e_run.json"

if [[ ! -f "$SYNC_SH" ]]; then
  echo "ERROR: sync_workspace_artifacts.sh not found under CURSOR_ROOT=$CURSOR_ROOT"
  echo "Set SYNC_SH to the full path of sync_workspace_artifacts.sh, or widen CURSOR_ROOT."
  exit 1
fi

if [[ ! -f "$JOB_JSON" ]]; then
  echo "ERROR: job JSON not found: $JOB_JSON"
  exit 1
fi

echo "== Sync (PROFILE=$PROFILE WORKSPACE_PATH=$WORKSPACE_PATH) =="
PROFILE="$PROFILE" WORKSPACE_PATH="$WORKSPACE_PATH" "$SYNC_SH" \
  "$REPO_ROOT/notebooks/01_setup_data.ipynb" \
  "$REPO_ROOT/notebooks/02_create_genie_spaces.ipynb" \
  "$REPO_ROOT/notebooks/03_genie_evals_benchmarks.ipynb" \
  "$REPO_ROOT/notebooks/04_talk_with_data.ipynb" \
  "$REPO_ROOT/notebooks/05_genie_code_skills.ipynb" \
  "$REPO_ROOT/notebooks/06_compare_genie_spaces.ipynb" \
  "$REPO_ROOT/notebooks/07_security_governance.ipynb" \
  "$REPO_ROOT/notebooks/08_deployment_best_practices.ipynb" \
  "$REPO_ROOT/notebooks/09_monitoring_observability.ipynb"

# App sources must land under WORKSPACE_PATH/app/ so notebook 08 can export app/app.py, etc.
echo "== Sync Databricks App bundle (WORKSPACE_PATH=$WORKSPACE_PATH/app) =="
PROFILE="$PROFILE" WORKSPACE_PATH="$WORKSPACE_PATH/app" "$SYNC_SH" \
  "$REPO_ROOT/app/app.py" \
  "$REPO_ROOT/app/app.yaml" \
  "$REPO_ROOT/app/requirements.txt"

echo "== Submit E2E (no-wait) =="
OUT="$(databricks jobs submit -p "$PROFILE" --no-wait --timeout 240m --json @"$JOB_JSON" -o json)"
RUN_ID="$(python3 -c "import json,sys; print(json.loads(sys.argv[1])['run_id'])" "$OUT")"
echo "run_id=$RUN_ID"

echo "== Poll every ${POLL_SECS}s (max ${MAX_ITERS} iters) =="
for ((i = 1; i <= MAX_ITERS; i++)); do
  databricks jobs get-run -p "$PROFILE" "$RUN_ID" -o json > "$E2E_RUN_JSON"
  LC="$(python3 -c "import json; d=json.load(open('$E2E_RUN_JSON')); print(d.get('state',{}).get('life_cycle_state',''))")"
  RS="$(python3 -c "import json; d=json.load(open('$E2E_RUN_JSON')); print(d.get('state',{}).get('result_state','') or '')")"
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) iter=$i lifecycle=$LC result=$RS"
  if [[ "$LC" == "TERMINATED" || "$LC" == "INTERNAL_ERROR" ]]; then
    python3 -c "import json; d=json.load(open('$E2E_RUN_JSON')); print((d.get('state',{}).get('state_message') or '')[:500])"
    python3 -c "import json; d=json.load(open('$E2E_RUN_JSON')); tasks=d.get('tasks',[]); [print(t.get('task_key'), t.get('state',{}).get('result_state')) for t in sorted(tasks, key=lambda x: x.get('task_key',''))]"
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
