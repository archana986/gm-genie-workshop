"""One-off builder: writes notebooks/02_create_genie_spaces.ipynb (run from repo root)."""
import base64
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_GENIE_TEMPLATE_B64 = base64.b64encode(
    (ROOT / "templates" / "manufacturing_genie_configured.json").read_bytes()
).decode("ascii")
OUT = ROOT / "notebooks" / "02_create_genie_spaces.ipynb"

cells = []


def md(lines):
    cells.append({"cell_type": "markdown", "metadata": {}, "source": [l + "\n" for l in lines[:-1]] + [lines[-1]]})

def code(src: str):
    lines = [ln + "\n" for ln in src.strip().split("\n")]
    if lines:
        lines[-1] = lines[-1].rstrip("\n")
        if not lines[-1].endswith("\n"):
            lines[-1] += "\n"
    cells.append({"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": lines})

md([
    "# Step 2 — Create Genie spaces with information (Notebook 02)",
    "",
    "Nine-step workshop: **1** data → **2** this notebook → **3** evals/benchmarks → **4** talk → **5** skills / no-eval space → **6** compare → **7** security → **8** deployment → **9** monitoring.",
    "",
    "Creates **three** Genie spaces on the same manufacturing tables:",
    "",
    "1. **Blank context** — tables only, minimal instructions.",
    "2. **Configured (with examples)** — full business instructions + **sample questions** and **curated Q→SQL** from `templates/manufacturing_genie_configured.json` (primary: `genie_space_id`).",
    "3. **Configured (no examples)** — **same** business instructions as (2) but **no** sample/curated pairs (`genie_space_id_configured_no_evals`) for A/B in notebook **06**.",
    "",
    "Saves IDs to `workshop_config`. Next: **03_genie_evals_benchmarks**.",
    "",
    "**Prerequisite:** Run `01_setup_data` first.",
])

md([
    "## Serverless compute",
    "",
    "Attach **Serverless** notebook compute. The notebook uses the Databricks **SDK** and `spark` only for the final `workshop_config` table; config stays in **Python variables** (no `spark.conf.set` for custom keys).",
])

md([
    "## Configuration",
    "",
    "Set **Catalog** and **Schema** to match **notebook 01** (your Unity Catalog location for this workshop). The widget defaults are **examples only**—replace them with your catalog and schema before running in a customer workspace.",
    "",
    "All later notebooks use the **same** widget names so the path stays consistent.",
])

code("""
dbutils.widgets.text("catalog", "workshop_demo", "Catalog")
dbutils.widgets.text("schema", "genie_workshop_manufacturing", "Schema")

CATALOG = dbutils.widgets.get("catalog")
SCHEMA = dbutils.widgets.get("schema")
fqn = f"{CATALOG}.{SCHEMA}"

SPACE_TITLE_BLANK = "Manufacturing workshop — blank context"
SPACE_TITLE_CONFIGURED = "Manufacturing workshop — configured"
SPACE_TITLE_CONFIGURED_NO_EX = "Manufacturing workshop — configured, no example SQL"
SPACE_DESC_BLANK = "Manufacturing tables only. Minimal instructions for A/B comparison."
SPACE_DESC_CONFIGURED = "Manufacturing quality analytics: OEE, FPY, defects, downtime, safety, equipment feedback."
SPACE_DESC_CONFIGURED_NO_EX = (
    "Same instructions as configured space but no sample questions or curated Q→SQL pairs (benchmark against full context in 03)."
)

print(f"Target data: {fqn}")
""")

md([
    "## SQL warehouse",
    "",
    "Genie needs a **SQL warehouse**. This cell picks a running, starting, or serverless warehouse.",
])

code("""
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
warehouses = list(w.warehouses.list())
warehouse_id = None

for wh in warehouses:
    state = str(wh.state).upper() if wh.state else ""
    if state in ("RUNNING", "STARTING"):
        warehouse_id = wh.id
        print(f"Using warehouse: {wh.name} ({wh.id}) state={state}")
        break

if not warehouse_id:
    for wh in warehouses:
        if getattr(wh, "enable_serverless_compute", False) or "serverless" in (wh.name or "").lower():
            warehouse_id = wh.id
            print(f"Using serverless warehouse: {wh.name} ({wh.id})")
            break

if not warehouse_id and warehouses:
    wh = warehouses[0]
    warehouse_id = wh.id
    print(f"Using first warehouse: {wh.name} ({wh.id}) state={wh.state}")

if not warehouse_id:
    raise RuntimeError("No SQL warehouse found. Create or start one, then re-run.")
""")

md([
    "## Load configured Genie JSON",
    "",
    "Load order: **local / Repo paths** → optional **workspace export** (widget path and `/Users/...` alias) → **embedded** copy of `templates/manufacturing_genie_configured.json` (base64 in this notebook so **Jobs always work**). Re-run `scripts/build_02_notebook.py` after editing the template to refresh the embedded copy.",
])

_LOAD_GENIE_JSON_CELL_PREFIX = '''import base64
import json
import os

import requests
from databricks.sdk import WorkspaceClient

dbutils.widgets.text(
    "genie_json_path",
    "manufacturing_genie_configured.json",
    "Local/Repo relative path to manufacturing_genie_configured.json",
)
dbutils.widgets.text(
    "genie_json_workspace_path",
    "",
    "Workspace path for export fallback",
)

_EMBEDDED_B64 = "'''

_LOAD_GENIE_JSON_CELL_SUFFIX = '''"


def _load_embedded():
    return json.loads(base64.b64decode(_EMBEDDED_B64).decode("utf-8"))


_wc = WorkspaceClient()
_host = _wc.config.host.rstrip("/")
_headers = {**_wc.config.authenticate()}


def _load_json_via_export(abs_workspace_path: str):
    r = requests.get(
        f"{_host}/api/2.0/workspace/export",
        headers=_headers,
        params={"path": abs_workspace_path, "format": "SOURCE"},
        timeout=60,
    )
    if r.status_code != 200:
        raise RuntimeError(f"export HTTP {r.status_code}: {r.text[:300]}")
    body = r.json()
    b64 = body.get("content")
    if not b64:
        raise RuntimeError("export response missing content")
    raw = base64.b64decode(b64)
    text = raw.decode("utf-8-sig").strip()
    if not text:
        raise RuntimeError("export decoded empty body")
    return json.loads(text)


def _try_open_local(p):
    if not p:
        return None
    try:
        with open(p) as f:
            return json.load(f)
    except (OSError, IOError, FileNotFoundError, json.JSONDecodeError):
        return None


path_try = [
    dbutils.widgets.get("genie_json_path").strip(),
    "manufacturing_genie_configured.json",
    "templates/manufacturing_genie_configured.json",
    "../templates/manufacturing_genie_configured.json",
]

genie_config = None
used = None
for p in path_try:
    genie_config = _try_open_local(p)
    if genie_config is not None:
        used = p
        break

ws = dbutils.widgets.get("genie_json_workspace_path").strip()
if genie_config is None and ws:
    candidates = [ws]
    if ws.startswith("/Workspace/Users"):
        candidates.append(ws[len("/Workspace") :])
    elif ws.startswith("/Users/"):
        candidates.append("/Workspace" + ws)
    last_err = None
    for ap in dict.fromkeys(candidates):
        try:
            genie_config = _load_json_via_export(ap)
            used = ap + " (workspace export)"
            last_err = None
            break
        except Exception as e:
            last_err = e
    if genie_config is None and last_err:
        print("Workspace export failed, using embedded template:", str(last_err)[:200])

if genie_config is None:
    genie_config = _load_embedded()
    used = "embedded template (refresh: python3 scripts/build_02_notebook.py)"

print(f"Loaded Genie template from: {used}")

OLD_FQN = "main.manufacturing_quality_analytics"


def rewrite_fqn(obj):
    if isinstance(obj, str):
        return obj.replace(OLD_FQN, fqn)
    if isinstance(obj, list):
        return [rewrite_fqn(x) for x in obj]
    if isinstance(obj, dict):
        return {k: rewrite_fqn(v) for k, v in obj.items()}
    return obj


genie_config = rewrite_fqn(genie_config)
'''

code(_LOAD_GENIE_JSON_CELL_PREFIX + _GENIE_TEMPLATE_B64 + _LOAD_GENIE_JSON_CELL_SUFFIX)

md([
    "## Helpers: build API payload and create space",
    "",
    "Uses the **Genie spaces** REST API (`/api/2.0/genie/spaces`) with `serialized_space`. **Browser links** must use **`/genie/rooms/<space_id>?o=<workspace>`** (see `genie_ui_room_url` in code—not `/genie/spaces/`, which breaks navigation).",
])

code("""
import json
import re
import uuid
import requests

host = w.config.host.rstrip("/")
headers = {**w.config.authenticate(), "Content-Type": "application/json"}


def genie_ui_room_url(space_id: str) -> str:
    # Genie UI (clickable in browser): /genie/rooms/<space_id>?o=<workspace_id>
    # On Azure Databricks, workspace id matches adb-<id> in the hostname. REST APIs still use /api/2.0/genie/spaces/...
    m = re.search(r"adb-(\\d+)\\.", host)
    o = m.group(1) if m else ""
    q = f"?o={o}" if o else ""
    return f"{host}/genie/rooms/{space_id}{q}"


TABLE_IDENTIFIERS = sorted(
    [
        f"{fqn}.production_lines",
        f"{fqn}.operators",
        f"{fqn}.production_events",
        f"{fqn}.plants",
        f"{fqn}.quality_metrics_daily",
        f"{fqn}.safety_incidents",
        f"{fqn}.equipment_feedback",
    ]
)

tables_config = [{"identifier": t} for t in TABLE_IDENTIFIERS]


def build_serialized_blank():
    blank_instr = (
        "You answer questions using SQL against the attached tables only. "
        "Use fully qualified table names. "
        "Do not invent business rules or thresholds unless they appear in column values."
    )
    return json.dumps(
        {
            "version": 2,
            "config": {"sample_questions": []},
            "data_sources": {"tables": tables_config},
            "instructions": {
                "text_instructions": [{"content": [blank_instr]}],
                "example_question_sqls": [],
            },
        }
    )


def build_serialized_configured():
    sql_instr = genie_config.get("sql_instructions", "")
    curated = genie_config.get("curated_questions", [])
    curated_qs = []
    for q in curated:
        curated_qs.append(
            {
                "id": uuid.uuid4().hex,
                "question": [q["question"]],
                "sql": [q["sql"]],
            }
        )
    curated_qs.sort(key=lambda x: x["id"])
    sample = genie_config.get("sample_questions", [])
    sample_qs = [{"id": uuid.uuid4().hex, "question": [sq]} for sq in sample]
    sample_qs.sort(key=lambda x: x["id"])
    return json.dumps(
        {
            "version": 2,
            "config": {"sample_questions": sample_qs},
            "data_sources": {"tables": tables_config},
            "instructions": {
                "text_instructions": [{"content": [sql_instr]}],
                "example_question_sqls": curated_qs,
            },
        }
    )


def build_serialized_configured_no_examples():
    # Same text instructions as configured; no sample Qs or curated Q-to-SQL pairs.
    sql_instr = genie_config.get("sql_instructions", "")
    return json.dumps(
        {
            "version": 2,
            "config": {"sample_questions": []},
            "data_sources": {"tables": tables_config},
            "instructions": {
                "text_instructions": [{"content": [sql_instr]}],
                "example_question_sqls": [],
            },
        }
    )


def list_spaces():
    r = requests.get(f"{host}/api/2.0/genie/spaces", headers=headers)
    r.raise_for_status()
    return r.json().get("spaces", [])


def create_genie_space(title, description, serialized_space_str):
    for s in list_spaces():
        if s.get("title") == title:
            sid = s.get("space_id") or s.get("id")
            print(f"Already exists: {title!r} -> {sid}")
            return sid, genie_ui_room_url(sid)

    body = {
        "title": title,
        "description": description,
        "warehouse_id": warehouse_id,
        "serialized_space": serialized_space_str,
    }
    resp = requests.post(
        f"{host}/api/2.0/genie/spaces",
        headers=headers,
        json=body,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Genie create failed {resp.status_code}: {resp.text[:800]}")

    sid = resp.json().get("space_id") or resp.json().get("id")
    print(f"Created: {title!r} -> {sid}")
    return sid, genie_ui_room_url(sid)
""")

md([
    "## Create blank, configured, and configured-without-example-SQL spaces",
    "",
    "If creation fails (permissions or API shape), use the UI: **New > Genie space**, attach the seven tables, then insert IDs manually into `workshop_config` (see next cell).",
])

code("""
blank_id, blank_url = create_genie_space(
    SPACE_TITLE_BLANK,
    SPACE_DESC_BLANK,
    build_serialized_blank(),
)

cfg_id, cfg_url = create_genie_space(
    SPACE_TITLE_CONFIGURED,
    SPACE_DESC_CONFIGURED,
    build_serialized_configured(),
)

cfg_noex_id, cfg_noex_url = create_genie_space(
    SPACE_TITLE_CONFIGURED_NO_EX,
    SPACE_DESC_CONFIGURED_NO_EX,
    build_serialized_configured_no_examples(),
)

print("Blank URL:", blank_url)
print("Configured (with examples) URL:", cfg_url)
print("Configured (no example SQL) URL:", cfg_noex_url)
""")

md([
    "## Save IDs to `workshop_config`",
    "",
    "- **`genie_space_id`** / **`genie_space_id_configured`** — configured space **with** sample + curated SQL.",
    "- **`genie_space_id_configured_no_evals`** — configured space **without** those examples (instructions only).",
    "- **`genie_space_id_blank`** — minimal-instructions baseline.",
])

code("""
from pyspark.sql import Row

rows = [
    Row(
        key="genie_space_id",
        value=cfg_id,
        space_name=SPACE_TITLE_CONFIGURED,
        space_url=cfg_url,
    ),
    Row(
        key="genie_space_id_configured",
        value=cfg_id,
        space_name=SPACE_TITLE_CONFIGURED,
        space_url=cfg_url,
    ),
    Row(
        key="genie_space_id_configured_no_evals",
        value=cfg_noex_id,
        space_name=SPACE_TITLE_CONFIGURED_NO_EX,
        space_url=cfg_noex_url,
    ),
    Row(
        key="genie_space_id_blank",
        value=blank_id,
        space_name=SPACE_TITLE_BLANK,
        space_url=blank_url,
    ),
]

spark.createDataFrame(rows).write.mode("overwrite").saveAsTable(f"{fqn}.workshop_config")
display(spark.table(f"{fqn}.workshop_config"))
print("Done. Primary genie_space_id -> configured (with examples). Use genie_space_id_configured_no_evals in 06 for A/B.")
""")

md([
    "## Open Genie in the browser (clickable links)",
    "",
    "Links below are rebuilt from your **current workspace host** and each row’s **space id** (`value`). Use these—not manual copies of old URLs—if a link ever 404s after an upgrade.",
])

code("""
import html

for _r in (
    spark.sql(
        f"SELECT key, value, space_name FROM {fqn}.workshop_config ORDER BY key"
    ).collect()
):
    _u = genie_ui_room_url(_r["value"])
    displayHTML(
        "<p><b>"
        + html.escape(str(_r["key"]))
        + "</b> &mdash; "
        + "<a href=\\""
        + html.escape(_u, quote=True)
        + "\\" target=\\"_blank\\" rel=\\"noopener\\">"
        + html.escape(str(_r["space_name"]))
        + "</a><br/><code style=\\"font-size:11px\\">"
        + html.escape(_u)
        + "</code></p>"
    )
""")

md([
    "## Next steps",
    "",
    "- Open the three URLs; try the same question across blank vs primary vs no-example space.",
    "- **`03_genie_evals_benchmarks`** — define suite, verify SQL, push BENCHMARK rows to the primary space.",
    "- **`04`–`06`** — explore, skills, then **compare** with vs without in-space examples.",
    "- **`07`–`09`** — security, deployment patterns, monitoring.",
])

nb = {
    "nbformat": 4,
    "nbformat_minor": 0,
    "metadata": {
        "language_info": {"name": "python"},
        "application/vnd.databricks.v1+notebook": {
            "language": "python",
            "notebookMetadata": {"pythonIndentUnit": 4},
            "notebookName": "02_create_genie_spaces",
            "computePreferences": {
                "hardware": {
                    "accelerator": None,
                    "gpuPoolId": None,
                    "memory": None,
                }
            },
            "dashboards": [],
            "environmentMetadata": {
                "base_environment": "",
                "environment_version": "4",
            },
            "widgets": {},
        },
    },
    "cells": cells,
}

OUT.write_text(json.dumps(nb, indent=1))
print("Wrote", OUT)
