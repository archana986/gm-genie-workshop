# How the workshop code works

This document explains **what the notebooks do under the hood**. For prerequisites and run order, see [SETUP.md](./SETUP.md). For outcomes and packaging, see [README.md](./README.md).

## Notebook 01 — `01_setup_data`

- **Spark / SQL:** Creates the UC schema if needed, then Delta tables for plants, lines, operators, events, quality metrics, safety, equipment feedback.
- **Data:** Synthetic rows via Faker-style generation in Spark; deterministic enough for benchmarks.
- **Genie support:** Table and column comments, plus SQL helper functions Genie can discover.
- **Config:** `dbutils` widgets for catalog and schema only (no `spark.conf.set` for workshop keys).

## Notebook 02 — `02_create_genie_spaces`

- **Template:** Decodes the **embedded** base64 JSON (maintainers regenerate from `templates/manufacturing_genie_configured.json` via `scripts/build_02_notebook.py`).
- **Rewrite:** Replaces placeholder FQN `main.manufacturing_quality_analytics` with `{CATALOG}.{SCHEMA}` everywhere in that template.
- **Warehouse:** Lists warehouses via `WorkspaceClient` and picks a usable id for Genie.
- **APIs:** Builds three `serialized_space` v2 payloads (blank, full context + examples, full context without example SQL), then `POST /api/2.0/genie/spaces` (with idempotent check by title).
- **Persistence:** Writes space ids and UI URLs into Delta table `{catalog}.{schema}.workshop_config` for downstream notebooks.

## Notebook 03 — `03_genie_evals_benchmarks`

- Reads primary Genie space id from `workshop_config`.
- Defines benchmark questions with expected numeric or structural checks.
- Uses Genie Conversation API (or documented patterns) to run questions and record pass/fail history in Delta.

## Notebook 04 — `04_talk_with_data`

- Resolves Genie links from `workshop_config`.
- Facilitator-oriented cells: open Genie in the browser, try NL questions, optional comparison to reference SQL.

## Notebook 05 — `05_genie_code_skills`

- Documents attaching **Genie Code** skills from `skill/manufacturing-genie-context/` (and related paths).
- Links skills workflow to the same spaces and tables.

## Notebook 06 — `06_compare_genie_spaces`

- Runs benchmarks (or subsets) against **configured with examples** vs **configured without examples** (and optionally blank) using ids stored in **02**.
- Highlights impact of in-space curated SQL and sample questions.

## Notebook 07 — `07_security_governance`

- **Unity Catalog:** Creates masked or restricted views (e.g. sensitive unit id column).
- **Genie:** Points a demo space or instructions at the restricted view for non-admin principals.

## Notebook 08 — `08_deployment_best_practices`

- **Operational patterns:** Playground, Jobs scheduling for refresh, optional **Databricks App** bundle under `app/`.
- **CI/CD (optional):** Export/remap serialized space definitions across environments (documentation and sample fragments).

## Notebook 09 — `09_monitoring_observability`

- **Observability:** Links to Genie monitoring where available; SQL examples for audit and query history system tables.
- **History:** Reads benchmark run history from Delta written in earlier steps.

## Maintainer scripts (not required for learners)

| Script | Role |
|--------|------|
| `scripts/build_02_notebook.py` | Embeds `templates/manufacturing_genie_configured.json` into **02**. |
| `scripts/verify_02_embedded_template.py` | Confirms embedded blob matches the template file. |
| `scripts/build_notebooks_03_08.py` | Regenerates notebooks 03–09 from Python sources (if you use that workflow). |
| `scripts/e2e_sync_submit_poll.sh` | Internal sync + multi-task job smoke test. |
