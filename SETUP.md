# Workshop setup

Use this file **before and during** the first full run. It covers **environment and verification**, not marketing copy.

**Related docs**

| Doc | Use it for |
|-----|------------|
| [README.md](./README.md) | What the workshop is, what each notebook achieves, outcomes, package contents |

## 1. Prerequisites

- Databricks workspace with **Unity Catalog**, **Genie**, and **Serverless** (or UC-enabled) notebook compute.
- Permission to **create a schema** and **write tables** in a catalog you control (create the catalog in Catalog Explorer if jobs cannot create catalogs).
- At least one **SQL warehouse** (running, starting, or serverless-capable). Notebook **02** auto-selects one.
- Same **Catalog** and **Schema** widget values in **every** notebook from **01** through **09**.

Example widget defaults in the notebooks (`workshop_demo`, `genie_workshop_manufacturing`) are for quick facilitator dry-runs—**change them** to your UC location for customer workspaces.

## 2. Importing the workshop

- **Databricks Repos:** Clone this repository; open `notebooks/` in order.
- **Upload:** Import the `notebooks/` folder (or individual `.ipynb` files). You do **not** need to upload any Genie JSON for **02**; the template is **embedded** in the notebook.

Optional folders:

- **`app/`** — only if you follow notebook **08** (Databricks App).
- **`skill/`** — only if you follow notebook **05** (Genie Code skills).

The file **`templates/manufacturing_genie_configured.json`** is for **maintainers** who edit instructions and regenerate notebook **02** (see section 4). Customers do not need it in the workspace.

## 3. First-time run checklist

1. Run **01** top to bottom. After **`%pip`**, Python restarts—run the **re-set config** cell, then continue.
2. Run **02** through the **Load configured Genie template** code cell. You should see output starting with:
   - **`Loaded Genie template from: embedded`**
3. Finish **02** until `workshop_config` exists and links print for the three Genie spaces.
4. Run **03 → 09** in order at least once.

## 4. Maintainer: embedded template in notebook 02

The configured Genie space (instructions, sample questions, curated SQL) is **shipped inside** `02_create_genie_spaces.ipynb` as base64 so Jobs and minimal imports always work.

**Source of truth in Git:** `templates/manufacturing_genie_configured.json`

After editing that JSON:

```bash
python3 scripts/build_02_notebook.py
```

Then confirm the notebook still matches the file:

```bash
python3 scripts/verify_02_embedded_template.py
```

Expected: `OK: embedded template in 02 matches templates/manufacturing_genie_configured.json`

## 5. Notebook-specific setup notes

- **07 — Security:** SQL references a group name such as `admin_group`. Replace with a real group in your workspace, or adjust the masking logic.
- **08 — App:** Deploy only if `app.py`, `app.yaml`, and `requirements.txt` are available to the App (see notebook **08**).
- **09 — Monitoring:** Queries against `system.access.audit` and `system.query.history` need grants; the notebook handles missing access gracefully.

## 6. Troubleshooting

| Symptom | Check |
|--------|--------|
| **02** cannot create spaces | Genie entitlement, warehouse id, and API permissions for your user. |
| Wrong catalog in Genie answers | **02** rewrites template placeholders from `main.manufacturing_quality_analytics` to your `CATALOG.SCHEMA`; ensure widgets match **01**. |
| **01** fails after pip | Re-run the post-restart config cell with the same catalog/schema. |
