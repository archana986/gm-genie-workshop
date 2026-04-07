# GM Genie Workshop

Hands-on **Databricks Genie** lab for **manufacturing** analytics—OEE, quality, downtime, and safety. You choose a Unity Catalog **catalog** and **schema** once; every notebook and the optional end-to-end job use the same values.

## Parameterization (requirement checklist)

| Expectation | How it is met |
|-------------|----------------|
| Same **Catalog** / **Schema** across the path | Notebooks **01–09** define `dbutils.widgets.text("catalog", ...)` and `dbutils.widgets.text("schema", ...)` and build `fqn = f"{CATALOG}.{SCHEMA}"` (or equivalent) for tables, views, and `workshop_config`. |
| Defaults are examples only | Default widget values (`gm_ama_demos`, `genie_workshop_manufacturing`) match the reference AI Query workspace; customers replace with their UC location before teaching. |
| Automation (Jobs) | `scripts/job_submit_gm_genie_e2e_01_09.json` passes the same `catalog` and `schema` as `base_parameters` on **every** task so serverless runs match manual widget runs. |
| Genie template | `templates/manufacturing_genie_configured.json` uses placeholders rewritten in **02** to the widget catalog/schema (`rewrite_fqn` in the builder). |

**Not parameterized (by design):** workspace host, warehouse choice (resolved at runtime via APIs where coded), and external links in docs. **07** uses `is_member('admin_group')` for masking demos—customers must align group name or adjust the view.

**Regenerate warning:** `python3 scripts/build_notebooks_03_08.py` **rewrites notebooks 03–09** from the Python builder. Extended **08** (CI/CD Option D) and **09** (monitoring parts) are maintained in the checked-in `.ipynb` files; re-run the builder only if you have ported those sections into `scripts/build_notebooks_03_08.py`.

## Nine-step flow (recommended order)

| Step | Notebook | Purpose |
|------|----------|---------|
| 1 | `01_setup_data` | UC tables, synthetic data, functions, comments; **`unit_serial_vin`** for security demo |
| 2 | `02_create_genie_spaces` | Blank + configured + no-example Genie spaces; `workshop_config` |
| 3 | `03_genie_evals_benchmarks` | Benchmark suite, ground-truth SQL, **BENCHMARK** rows on primary space |
| 4 | `04_talk_with_data` | Genie UI exploration; reference SQL vs Genie |
| 5 | `05_genie_code_skills` | Genie Code skills; links to no-eval space |
| 6 | `06_compare_genie_spaces` | A/B benchmarks; **`genie_benchmark_runs`** |
| 7 | `07_security_governance` | Masked **`production_events_restricted`** + Genie Data Room proof |
| 8 | `08_deployment_best_practices` | Clickable workspace links (incl. Genie **Monitoring** deep link), materialize **Databricks App** bundle, Jobs pattern, **Option D — CI/CD** |
| 9 | `09_monitoring_observability` | Monitoring tab link, **benchmark history** (aligned to `genie_benchmark_runs` columns), **audit** (`aibiGenie`), **query history**, improvement loop, community tools, privacy |

**Compute:** **Serverless** notebook compute. Use **Python variables / widgets** only (no `spark.conf.set` for custom application keys).

## Sync to a customer workspace

Use the shared sync script from the repo root. Set **`PROFILE`** to a name in `~/.databrickscfg` (match workspace **host** to the right profile when using multiple workspaces) and **`WORKSPACE_PATH`** to the folder where notebooks live.

### Existing folders and overwrite

Each import uses **`databricks workspace import … --overwrite`**. That means:

- **Notebooks and files at the target path are replaced** by the version from this repo (same notebook name → updated content).
- **Nothing outside the listed paths is deleted**—other objects in the same folder stay as they are.
- **Delta tables and `workshop_config` in Unity Catalog are not touched by sync**; they change only when you **run** the notebooks (for example **01** and **02**).
- The **app** bundle syncs into **`WORKSPACE_PATH/app/`** (second command below), overwriting `app`, `app.yaml`, and `requirements.txt` there if they already exist.

Use a **dedicated workspace folder** per customer or environment if you need a clean boundary.

```bash
PROFILE="azure-aiquery" WORKSPACE_PATH="/Workspace/Users/you@company.com/GM-Genie-Workshop" \
  ./Customer-Work/AMA-GM/sync_workspace_artifacts.sh \
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

# Databricks App sources for notebook 08 Option B (must live under WORKSPACE_PATH/app/)
PROFILE="azure-aiquery" WORKSPACE_PATH="/Workspace/Users/you@company.com/GM-Genie-Workshop/app" \
  ./Customer-Work/AMA-GM/sync_workspace_artifacts.sh \
  "Customer-Work/GM-Genie-Workshop/app/app.py" \
  "Customer-Work/GM-Genie-Workshop/app/app.yaml" \
  "Customer-Work/GM-Genie-Workshop/app/requirements.txt"
```

`scripts/e2e_sync_submit_poll.sh` runs **both** sync steps automatically.

Edit **`scripts/job_submit_gm_genie_e2e_01_09.json`** notebook paths if your workspace folder differs. To run against another catalog/schema, change **`base_parameters`** on each task consistently.

## E2E: sync + submit + poll

From the **Cursor** root (folder that contains `Customer-Work/`):

```bash
bash Customer-Work/GM-Genie-Workshop/scripts/e2e_sync_submit_poll.sh
```

Optional: `PROFILE`, `WORKSPACE_PATH`, `CURSOR_ROOT`, `POLL_SECS`, `MAX_ITERS`.

Single-shot submit (after sync):

```bash
databricks jobs submit -p azure-aiquery --no-wait --timeout 240m \
  --json @"Customer-Work/GM-Genie-Workshop/scripts/job_submit_gm_genie_e2e_01_09.json"
```

**Validation:** The bundled nine-task serverless job has been run end-to-end against the reference workspace after syncing the artifacts above; all notebook tasks completed **SUCCESS** (lifecycle `TERMINATED`, result `SUCCESS`). Re-run in your workspace after changing `catalog` / `schema` in the job JSON.

## Known gaps / permissions

- **`system.access.audit`** and **`system.query.history`**: may fail without metastore admin or grants; notebooks catch errors and explain.
- **Genie REST export (08)**: response shape can vary; Phase 1 normalizes `serialized_space` string vs dict. **POST** deploy may return non-200 without Genie create permissions—handled with a message.
- **Notebook 09** `system.query.history`: uses **`total_duration_ms`**, **`executed_by`**, **`produced_rows`** per the [query history system table](https://docs.databricks.com/aws/en/admin/system-tables/query-history) schema (not `duration_ms` / `user_name` / `rows_produced`).
- **07 masking**: demonstrate with a user **not** in `admin_group`, or VINs remain visible.

## Regenerate notebooks (02 only, or 03–08 from builder)

```bash
cd Customer-Work/GM-Genie-Workshop
python3 scripts/build_02_notebook.py
# Overwrites 03–09 when you intentionally sync the builder:
python3 scripts/build_notebooks_03_08.py
```

## Docs

| File | Purpose |
|------|---------|
| [REQUIREMENTS.md](./REQUIREMENTS.md) | Scope and acceptance criteria |
| [PLAN.md](./PLAN.md) | Phased build |
