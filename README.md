# Databricks Genie Workshop — Manufacturing Quality Analytics

A hands-on workshop that teaches you how to build, evaluate, secure, deploy,
and monitor a Databricks Genie space using a manufacturing quality dataset.

## Prerequisites

- Databricks workspace with **Unity Catalog** and **Genie** enabled
- A catalog and schema where you have `CREATE TABLE`, `CREATE VOLUME`, and `CREATE FUNCTION` permissions
- A running **SQL warehouse** (serverless or Pro)
- **Serverless** notebook compute (or a classic cluster with Unity Catalog access)

## Getting started

1. Import the **`notebooks/`** folder into your Databricks workspace.
2. Import the **`templates/`** folder into the **same parent directory** as `notebooks/`.
3. Import the **`skill/`** folder into the **same parent directory** as `notebooks/`.

   Your workspace should look like this:

   ```
   /Workspace/Users/<your_email>/GM-Genie-Workshop/
     notebooks/                              (all 13 .ipynb files)
     templates/                              (Genie space template JSON)
       manufacturing_genie_configured.json
     skill/                                  (Genie Code skill files)
       manufacturing-analytics_genie/
         SKILL.md
   ```

4. Open **`00_workshop_config`** and set your **catalog** and **schema**.
5. Run notebooks **01** through **12** in order.

Every notebook reads your config automatically via `%run ./00_workshop_config`.

## First-run checklist

1. Run **01** (prebuild data) top to bottom. After `%pip`, Python restarts — run the **re-set config** cell, then continue.
2. Run **02** (setup data). Confirm tables and functions are created under your catalog.schema.
3. Run **03** (create Genie spaces). Confirm output shows three clickable Genie URLs and the `workshop_config` Delta table is written.
4. Run **04 → 12** in order.

## Notebooks

| # | Notebook | What you'll do |
|---|----------|---------------|
| 00 | Workshop Configuration | Set your catalog, schema, and preferences |
| 01 | Load Workshop Data | Create 7 manufacturing tables (plants, events, quality metrics, …) |
| 02 | Prepare Data | Build Delta tables, add column comments, create analytics functions |
| 03 | Create Genie Spaces | Create 3 Genie spaces: Blank, Configured (with examples), No Examples |
| 04 | Benchmarks & Evaluation | Define 16 benchmark questions and push them to Genie |
| 05 | Explore with Genie | Ask questions in the Genie UI and verify with reference SQL |
| 06 | Custom Skills | Extend Genie with domain-specific code skills |
| 07 | Compare Spaces (A/B) | Measure how curated Q-to-SQL examples improve accuracy |
| 08 | Security & Governance | Column masking with Unity Catalog — prove Genie respects it |
| 09 | Deploy an App | Wrap Genie in a branded Databricks App |
| 10 | Monitoring | Track accuracy, usage, and query performance over time |
| 11 | CI/CD (optional) | Promote Genie spaces across environments with code |
| 12 | Cleanup (optional) | Remove all workshop assets (spaces, app, tables, volume) |

## Notebook-specific setup notes

- **06 — Skills:** The skill file is included in `skill/manufacturing-analytics_genie/SKILL.md`. Before running notebook 06, copy this file into your workspace's `.assistant/skills/` directory so Genie Code can discover it.
- **08 — Security:** References a group name (`admin_group`). Replace with a real group in your workspace, or adjust the masking logic.
- **09 — App:** Requires `app/app.py`, `app.yaml`, and `requirements.txt` in the workspace. Import the `app/` folder alongside `notebooks/`.
- **10 — Monitoring:** Queries against `system.access.audit` and `system.query.history` need grants; the notebook handles missing access gracefully.

## Repository structure

```
├── notebooks/          13 workshop notebooks (00–12)
├── templates/          Genie space template JSON (used by notebooks 03 and 07)
│   └── manufacturing_genie_configured.json
├── skill/              Genie Code skill file (used by notebook 06)
│   └── manufacturing-analytics_genie/
│       └── SKILL.md
├── app/                Databricks App source (used by notebook 09)
│   ├── app.py
│   ├── app.yaml
│   └── requirements.txt
└── README.md           This file
```

## Compute

All notebooks run on **Serverless** compute. Classic clusters with Unity Catalog access also work.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Notebook 03 fails to create spaces | Check Genie entitlement, SQL warehouse availability, and API permissions for your user. |
| Wrong catalog in Genie answers | Notebook 03 rewrites template table references from `main.manufacturing_quality_analytics` to your `CATALOG.SCHEMA`. Ensure your widgets in notebook 00 match what you used in 01–02. |
| Notebook 01 fails after pip install | After `%pip`, Python restarts. Re-run the post-restart config cell with the same catalog/schema, then continue. |
| Notebook 07 `FileNotFoundError` | The `templates/` folder must be in the workspace at the same level as `notebooks/`. See "Getting started" above. |

## Maintainer notes

The configured Genie space template (instructions, sample questions, curated Q-to-SQL examples) lives in `templates/manufacturing_genie_configured.json`. Notebook 03 embeds this as base64 so Databricks Jobs work without extra file imports.

After editing the template JSON, regenerate the embedded copy:

```bash
python3 scripts/build_03_notebook.py
python3 scripts/verify_03_embedded_template.py
```

## License and data

Sample data is **synthetic** — generated for training and demos, not real production or customer data.
