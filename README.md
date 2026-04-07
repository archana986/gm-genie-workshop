# Manufacturing Genie — hands-on workshop

Self-contained **Databricks Genie** lab using **sample manufacturing data** (OEE, quality, downtime, safety). You run the notebooks **in your own workspace** on **your** Unity Catalog **catalog** and **schema**.

## What you receive

Unzip the package and import the notebooks into Databricks (for example: **Workspace** upload, **Repos**, or **Asset bundles**). Typical contents:

| Folder / files | Role |
|----------------|------|
| `notebooks/01` … `09` | Run in order (see below). |
| `templates/manufacturing_genie_configured.json` | **Optional.** Used by **02** if you place it where the notebook can read it. If it is missing, **02** uses a **built-in copy** of the same template. |
| `app/` | **Optional.** Only if you complete **08** “Databricks App” — copy `app/` next to your notebooks in the workspace (see **08**). |
| `skill/` | **Optional.** For **05** (Genie Code) — follow the instructions inside **05** to attach the skill. |

You do **not** need any external sync scripts or job JSON files to complete the workshop interactively.

### Folder layout (so everything works end-to-end)

Customers run notebooks **one after another** in **their** workspace. The workshop is designed for that flow.

- **Minimum to complete the core path (01 → 09):** the nine notebooks under `notebooks/`. Notebook **02** still works without any JSON on disk because it carries an **embedded** copy of the Genie template.
- **Recommended zip layout:** keep the same structure as this repo — `notebooks/` next to optional `templates/`, `app/`, `skill/`. That way **02** can optionally read `templates/manufacturing_genie_configured.json` from the driver when you use **Databricks Repos** or an uploaded folder tree.
- **Avoid:** importing only loose `.ipynb` files into a random workspace folder with **no** `templates/` sibling, if you expected file-based template loading; use the embedded path (leave workspace JSON widget empty) or upload the JSON and set the workspace-path widget.

## Before you run anything

- **Databricks** workspace with **Unity Catalog**, **Genie**, and **Serverless** (or UC-enabled) notebook compute.
- Permission to **create a schema** and **write tables** in a catalog you choose (or use an existing empty schema).
- A **SQL warehouse** available (Genie uses it); the notebooks pick one where possible.

## One setting for the whole workshop

Every notebook asks for the same two **widgets**:

- **Catalog**
- **Schema**

Set them to **your** UC location and use the **same values in every notebook** (01 through 09).

The notebooks ship with **example defaults** (`workshop_demo`, `genie_workshop_manufacturing`) so a facilitator can dry-run quickly. **Replace them with your catalog and schema** before customer use.

## Run order

| Step | Notebook | What it does |
|------|----------|----------------|
| 1 | `01_setup_data` | Creates tables and sample data; adds helper functions and comments Genie can use. |
| 2 | `02_create_genie_spaces` | Creates three Genie spaces and saves their IDs in a config table `workshop_config`. |
| 3 | `03_genie_evals_benchmarks` | Defines benchmarks and attaches them to your main Genie space. |
| 4 | `04_talk_with_data` | Opens Genie in the browser; optional “reference SQL” to compare answers. |
| 5 | `05_genie_code_skills` | Genie Code and optional skills; links to your spaces. |
| 6 | `06_compare_genie_spaces` | Compares benchmark results with vs without in-space examples. |
| 7 | `07_security_governance` | Unity Catalog masking / restricted view; Genie on the view only. |
| 8 | `08_deployment_best_practices` | Playground, optional App bundle, Jobs pattern, optional CI/CD demo. |
| 9 | `09_monitoring_observability` | Monitoring links, benchmark history, optional audit / query-history SQL. |

Run **01 → 09** at least once in that order the first time through.

## Notebook details worth knowing

- **Compute:** Use **Serverless** when prompted. Catalog and schema are set with **widgets** only (not `spark.conf.set` for workshop settings).
- **01:** After `%pip`, Python restarts — use the notebook’s “re-set config” cell, same catalog/schema.
- **02 — Genie template widgets:** The notebook loads `manufacturing_genie_configured.json` in this order: (1) **local paths** on the driver (default filename and `templates/…`—good for Repos or a zip layout), (2) **workspace file** only if you set the **workspace path** widget to a full `/Workspace/...` path, (3) **embedded copy** so it always works. **Leave the workspace-path widget empty** unless you uploaded the JSON yourself; see the **“Genie template file”** section at the top of **02** for full instructions. After the load cell runs, read **Loaded Genie template from:** in the output.
- **07:** The demo uses a group name `admin_group` in SQL — rename it to match **your** workspace group, or adjust the view logic.
- **08 — App:** If you use the App option, keep `app.py`, `app.yaml`, and `requirements.txt` together in a folder (for example `…/app/`) as **08** describes.
- **09:** Queries on `system.access.audit` and `system.query.history` need **appropriate grants**; cells catch errors if you do not have access.

## License and data

Sample data is **synthetic** for training and demos—not real production or customer data.
