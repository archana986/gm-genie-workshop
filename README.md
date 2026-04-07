# Manufacturing Genie — hands-on workshop

Self-contained **Databricks Genie** lab on **sample manufacturing data** (OEE, quality, downtime, safety). Participants run notebooks **in order** in **their** workspace using **their** Unity Catalog **catalog** and **schema**.

## How to use this documentation

| Document | Purpose |
|----------|---------|
| **This README** | Workshop overview, what each notebook **accomplishes**, **setup** and **expected outcomes**, and what ships in the package |
| **[SETUP.md](./SETUP.md)** | Step-by-step environment prep, first-run checklist, **verify embedded Genie template**, troubleshooting |

Start with **SETUP.md** before your first full run, then follow the notebook guide below.

## What you receive

| Folder / files | Role |
|----------------|------|
| `notebooks/01_setup_data.ipynb` … `09_monitoring_observability.ipynb` | **Required.** Run in order (see notebook guide below). |
| `templates/manufacturing_genie_configured.json` | **Maintainers only** — source for Genie instructions embedded in **02**. Learners do **not** upload this; **02** uses the built-in copy. After edits, run `python3 scripts/build_02_notebook.py` and `python3 scripts/verify_02_embedded_template.py`. |
| `app/` | **Optional** — notebook **08** (Databricks App). |
| `skill/` | **Optional** — notebook **05** (Genie Code skills). |

You do **not** need external sync scripts or job JSON to complete the workshop interactively.

### Package layout

Keep `notebooks/` together when you use Repos or zip import. Optional `app/` and `skill/` sit beside `notebooks/` if you use those modules.

## Global settings (all notebooks)

Every notebook uses the same two **widgets**:

- **Catalog**
- **Schema**

Use the **same values in 01–09**. Defaults (`workshop_demo`, `genie_workshop_manufacturing`) are for facilitator dry-runs—replace with your UC location for production workshops.

**Compute:** Prefer **Serverless**. Catalog/schema are widgets only (not `spark.conf.set` for workshop settings).

## Notebook guide (01 → 09)

For environment checks and verification commands, see **[SETUP.md](./SETUP.md)**.

| # | Notebook | What it accomplishes | Setup you need | Expected outcome |
|---|----------|----------------------|----------------|------------------|
| 01 | `01_setup_data` | Creates all manufacturing Delta tables, synthetic data, SQL helpers, and Genie-friendly comments. | UC catalog (exists or creatable), **CREATE SCHEMA** permission, Serverless/UC cluster. After `%pip`, re-run the post-restart config cell. | Tables and functions exist under your catalog.schema; notebook prints row counts / sanity checks. |
| 02 | `02_create_genie_spaces` | Creates **three** Genie spaces (blank, configured with examples, configured without examples) and saves ids to `workshop_config`. | **01** completed. SQL warehouse available. | Output includes **`Loaded Genie template from: embedded`**; three clickable Genie URLs; Delta table `{catalog}.{schema}.workshop_config` with keys such as `genie_space_id`, `genie_space_id_blank`, `genie_space_id_configured_no_evals`. |
| 03 | `03_genie_evals_benchmarks` | Defines evaluation benchmarks and attaches them to the primary Genie space. | **02** completed; primary space id in `workshop_config`. | Benchmark definitions stored; Genie eval integration ready for runs in **03** / **06**. |
| 04 | `04_talk_with_data` | Guided exploration in Genie UI; optional reference SQL. | **02**–**03** done; browser access to workspace. | You can open Genie from printed links and run sample questions. |
| 05 | `05_genie_code_skills` | Genie Code walkthrough; optional installation of skills from `skill/`. | **02** done; Genie Code enabled in workspace. | Skills path documented; exercises completed per notebook cells. |
| 06 | `06_compare_genie_spaces` | Compares benchmark behavior with vs without in-space examples. | **02**–**03** done; multiple space ids in `workshop_config`. | Side-by-side or sequential comparison results visible (pass rates or qualitative). |
| 07 | `07_security_governance` | UC masking / restricted view; Genie reads restricted data appropriately. | **01**–**02** done; adjust **`admin_group`** (or equivalent) to a real group. | View or mask in place; demo Genie space or instructions point at restricted objects. |
| 08 | `08_deployment_best_practices` | Playground, optional App, Jobs pattern, optional CI/CD notes. | **02** done; for App, `app/` files reachable from workspace. | Links work; optional App deploy path understood; reference job JSON named in notebook if used. |
| 09 | `09_monitoring_observability` | Monitoring links, benchmark history, optional system-table SQL. | Earlier notebooks run; **system** table access may be limited. | Printed links and/or SQL run or fail gracefully with documented fallbacks. |

## Quick reminders

- **01:** After `%pip`, Python restarts—use the notebook’s **re-set config** cell.
- **02:** Template is **embedded only**; success line must show **`Loaded Genie template from: embedded`**.
- **07:** Rename `admin_group` to match your workspace.
- **08:** Keep `app.py`, `app.yaml`, and `requirements.txt` together if you deploy the sample App.
- **09:** `system.access.audit` / `system.query.history` may require extra grants.

## License and data

Sample data is **synthetic** for training and demos—not real production or customer data.
