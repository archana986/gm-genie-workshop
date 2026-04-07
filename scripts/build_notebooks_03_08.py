#!/usr/bin/env python3
"""Generate notebooks 03–09 (workshop steps 3–9) and copy app assets for GM Genie Workshop."""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NB = ROOT / "notebooks"
# Sibling: Customer-Work/Vizient-Genie-Workshop/app
VIZ_APP = ROOT.parent / "Vizient-Genie-Workshop" / "app"

META = {
    "language_info": {"name": "python"},
    "application/vnd.databricks.v1+notebook": {
        "language": "python",
        "notebookMetadata": {"pythonIndentUnit": 4},
        "computePreferences": {
            "hardware": {"accelerator": None, "gpuPoolId": None, "memory": None}
        },
        "dashboards": [],
        "environmentMetadata": {"base_environment": "", "environment_version": "4"},
        "widgets": {},
    },
}


def nb(name, cells):
    META["application/vnd.databricks.v1+notebook"]["notebookName"] = name
    return {"nbformat": 4, "nbformat_minor": 0, "metadata": json.loads(json.dumps(META)), "cells": cells}


def md(*lines):
    src = "\n".join(lines) + "\n"
    return {"cell_type": "markdown", "metadata": {}, "source": [src]}


def code(src: str):
    lines = [ln + "\n" for ln in src.strip().split("\n")]
    if lines:
        lines[-1] = lines[-1].rstrip("\n") + "\n"
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": lines}


# --- 03 Evals & benchmarks: define suite, verify GT, push to Genie (step 3/9) ---
CELLS_03 = [
    md(
        "# Step 3 — Evals, benchmarks, and Genie space updates (manufacturing)",
        "",
        "Workshop flow: **1** data → **2** Genie space with information (notebook 02) → **3** this notebook → **4** talk to data → **5** skills / no-eval space → **6** compare → **7** security → **8** deployment → **9** monitoring.",
        "",
        "Here you **define** a benchmark suite, **verify** ground-truth SQL in Spark, and **push** BENCHMARK curated questions to the **primary** Genie space (`genie_space_id` from 02 — the space **with** sample questions and curated Q→SQL). That aligns Genie’s evaluation rail with questions you care about.",
        "",
        "**Next:** notebook **04** (explore in UI), **05** (skills), **06** (A/B test with vs without in-space examples).",
    ),
    md("## Serverless compute", "", "Use **Serverless**. Config uses **widgets** only (no `spark.conf.set` for custom keys)."),
    md(
        "## Benchmark design (best practices)",
        "",
        "- **Single scalar or simple aggregate** per question so Genie answers are easy to check automatically.",
        "- **Ground truth in Spark** using the same catalog/schema as production Genie tables (no hand-maintained numbers).",
        "- **Cover multiple grains**: counts, filtered counts, averages — and domain columns (OEE, events).",
        "- **Tie benchmarks to real user questions** you expect in Genie; retire or update when schema changes.",
        "- **Tolerance**: when you run automated checks (notebook 06), use a small relative band (for example 5%) for rounding vs Genie.",
        "- **Curated Q in the space** (from 02) teach style; **BENCHMARK** rows (this notebook) track regression-style checks in the data-rooms API when available.",
        "- If the API fails, add the same Q→SQL pairs manually under Genie **evaluation / benchmarks** in the UI.",
    ),
    md(
        "## Configuration",
        "",
        "Loads **`genie_space_id`** (configured space **with** examples). Re-run notebook **02** if missing.",
    ),
    code(
        '''
dbutils.widgets.text("catalog", "gm_ama_demos", "Catalog")
dbutils.widgets.text("schema", "genie_workshop_manufacturing", "Schema")

CATALOG = dbutils.widgets.get("catalog")
SCHEMA = dbutils.widgets.get("schema")
fqn = f"{CATALOG}.{SCHEMA}"

from databricks.sdk import WorkspaceClient
import html
import re
import requests

w = WorkspaceClient()
host = w.config.host.rstrip("/")
auth = {**w.config.authenticate(), "Content-Type": "application/json"}


def genie_ui_room_url(host: str, space_id: str) -> str:
    # Genie browser UI: /genie/rooms/<space_id>?o=<workspace_id> (not /genie/spaces/...)
    h = (host or "").rstrip("/")
    sid = str(space_id or "").strip()
    m = re.search(r"adb-(\\d+)\\.", h)
    o = m.group(1) if m else ""
    q = f"?o={o}" if o else ""
    return f"{h}/genie/rooms/{sid}{q}"


def _cfg(key):
    rows = spark.sql(
        f"SELECT value FROM {fqn}.workshop_config WHERE key = '{key}'"
    ).collect()
    return rows[0]["value"] if rows else None


SID_PRIMARY = _cfg("genie_space_id")
if not SID_PRIMARY:
    raise RuntimeError("Missing genie_space_id in workshop_config — run notebook 02.")
print("Primary Genie space (with examples):", SID_PRIMARY)
_ui = genie_ui_room_url(host, SID_PRIMARY)
print("Primary Genie UI URL (computed):", _ui)
displayHTML(
    '<p><a href="'
    + html.escape(_ui, quote=True)
    + '" target="_blank" rel="noopener">Open primary Genie space</a></p>'
)


def push_benchmarks(benchmarks_list, space_id, label=""):
    try:
        existing = requests.get(
            f"{host}/api/2.0/data-rooms/{space_id}/curated-questions",
            headers=auth,
            params={"question_type": "BENCHMARK"},
        ).json()
        for q in existing.get("curated_questions", []):
            qid = q.get("curated_question_id") or q.get("id") or q.get("question_id")
            if qid:
                requests.delete(
                    f"{host}/api/2.0/data-rooms/{space_id}/curated-questions/{qid}",
                    headers=auth,
                )
        ok = 0
        for b in benchmarks_list:
            r = requests.post(
                f"{host}/api/2.0/data-rooms/{space_id}/curated-questions",
                headers=auth,
                json={
                    "curated_question": {
                        "data_space_id": space_id,
                        "question_text": b["q"],
                        "question_type": "BENCHMARK",
                        "answer_text": b["sql"],
                        "is_deprecated": False,
                    },
                    "data_space_id": space_id,
                },
            )
            if r.status_code == 200:
                ok += 1
        print(f"{label}: pushed {ok}/{len(benchmarks_list)} benchmarks")
    except Exception as e:
        print(f"push_benchmarks skipped: {e}")


print("Helpers loaded")
'''
    ),
    md(
        "## Define benchmark suite",
        "",
        "**v2 — harder questions:** joins, filters, ratios, and subqueries so simple table scans are not enough. The **without-examples** space often scores lower than the primary space that has curated Q→SQL and benchmarks from this notebook. Re-run **03** after changing the list so BENCHMARK rows stay in sync.",
    ),
    code(
        '''
# Scalar ground truth only (notebook 06 parses one number from Genie’s result).
# Use YEAR(CAST(... AS DATE)) because event_date / date are strings in the seed data.

benchmarks_v1 = [
    {
        "q": "How many distinct production lines had at least one defect_detected event in calendar year 2024?",
        "sql": f"""SELECT CAST(COUNT(DISTINCT production_line_id) AS BIGINT) AS answer FROM {fqn}.production_events WHERE event_type = 'defect_detected' AND YEAR(CAST(event_date AS DATE)) = 2024""",
        "gt": f"SELECT CAST(COUNT(DISTINCT production_line_id) AS BIGINT) FROM {fqn}.production_events WHERE event_type = 'defect_detected' AND YEAR(CAST(event_date AS DATE)) = 2024",
    },
    {
        "q": "What is the sum of downtime_minutes from quality_metrics_daily for all rows in 2024 where the plant is in Michigan (join to plants by state)?",
        "sql": f"""SELECT CAST(ROUND(SUM(q.downtime_minutes), 0) AS BIGINT) AS answer FROM {fqn}.quality_metrics_daily q JOIN {fqn}.plants p ON q.plant_id = p.plant_id WHERE p.state = 'Michigan' AND YEAR(CAST(q.date AS DATE)) = 2024""",
        "gt": f"SELECT CAST(ROUND(SUM(q.downtime_minutes), 0) AS BIGINT) FROM {fqn}.quality_metrics_daily q JOIN {fqn}.plants p ON q.plant_id = p.plant_id WHERE p.state = 'Michigan' AND YEAR(CAST(q.date AS DATE)) = 2024",
    },
    {
        "q": "What is the total units_produced summed from quality_metrics_daily for January through March 2024 (Q1) only?",
        "sql": f"""SELECT CAST(SUM(q.units_produced) AS BIGINT) AS answer FROM {fqn}.quality_metrics_daily q WHERE CAST(q.date AS DATE) >= DATE '2024-01-01' AND CAST(q.date AS DATE) < DATE '2024-04-01'""",
        "gt": f"SELECT CAST(SUM(q.units_produced) AS BIGINT) FROM {fqn}.quality_metrics_daily q WHERE CAST(q.date AS DATE) >= DATE '2024-01-01' AND CAST(q.date AS DATE) < DATE '2024-04-01'",
    },
    {
        "q": "How many production lines had 500 or more unit_produced events in calendar year 2024?",
        "sql": f"""SELECT CAST(COUNT(*) AS BIGINT) AS answer FROM ( SELECT production_line_id FROM {fqn}.production_events WHERE event_type = 'unit_produced' AND YEAR(CAST(event_date AS DATE)) = 2024 GROUP BY production_line_id HAVING COUNT(*) >= 500 ) t""",
        "gt": f"SELECT CAST(COUNT(*) AS BIGINT) FROM ( SELECT production_line_id FROM {fqn}.production_events WHERE event_type = 'unit_produced' AND YEAR(CAST(event_date AS DATE)) = 2024 GROUP BY production_line_id HAVING COUNT(*) >= 500 ) t",
    },
    {
        "q": "How many safety incidents are both severity Critical and category Equipment Malfunction?",
        "sql": f"""SELECT CAST(COUNT(*) AS BIGINT) AS answer FROM {fqn}.safety_incidents WHERE severity = 'Critical' AND category = 'Equipment Malfunction'""",
        "gt": f"SELECT CAST(COUNT(*) AS BIGINT) FROM {fqn}.safety_incidents WHERE severity = 'Critical' AND category = 'Equipment Malfunction'",
    },
    {
        "q": "How many operators work at plants located in Michigan (use operators.plant_id joined to plants)?",
        "sql": f"""SELECT CAST(COUNT(*) AS BIGINT) AS answer FROM {fqn}.operators o JOIN {fqn}.plants p ON o.plant_id = p.plant_id WHERE p.state = 'Michigan'""",
        "gt": f"SELECT CAST(COUNT(*) AS BIGINT) FROM {fqn}.operators o JOIN {fqn}.plants p ON o.plant_id = p.plant_id WHERE p.state = 'Michigan'",
    },
    {
        "q": "For calendar year 2024 quality_metrics_daily only, what is the overall defect rate in percent rounded to a whole number: 100 times the sum of defects_found divided by the sum of units_produced?",
        "sql": f"""SELECT CAST(ROUND(100.0 * SUM(defects_found) / SUM(units_produced), 0) AS BIGINT) AS answer FROM {fqn}.quality_metrics_daily WHERE YEAR(CAST(date AS DATE)) = 2024""",
        "gt": f"SELECT CAST(ROUND(100.0 * SUM(defects_found) / SUM(units_produced), 0) AS BIGINT) FROM {fqn}.quality_metrics_daily WHERE YEAR(CAST(date AS DATE)) = 2024",
    },
    {
        "q": "How many production events in 2024 have event_type inspection_passed?",
        "sql": f"""SELECT CAST(COUNT(*) AS BIGINT) AS answer FROM {fqn}.production_events WHERE event_type = 'inspection_passed' AND YEAR(CAST(event_date AS DATE)) = 2024""",
        "gt": f"SELECT CAST(COUNT(*) AS BIGINT) FROM {fqn}.production_events WHERE event_type = 'inspection_passed' AND YEAR(CAST(event_date AS DATE)) = 2024",
    },
    {
        "q": "How many quality_metrics_daily rows in 2024 have oee_score strictly below 0.70?",
        "sql": f"""SELECT CAST(COUNT(*) AS BIGINT) AS answer FROM {fqn}.quality_metrics_daily WHERE YEAR(CAST(date AS DATE)) = 2024 AND oee_score < 0.70""",
        "gt": f"SELECT CAST(COUNT(*) AS BIGINT) FROM {fqn}.quality_metrics_daily WHERE YEAR(CAST(date AS DATE)) = 2024 AND oee_score < 0.70",
    },
    {
        "q": "What is the sum of employee_count for all plants in Texas?",
        "sql": f"""SELECT CAST(COALESCE(SUM(p.employee_count), 0) AS BIGINT) AS answer FROM {fqn}.plants p WHERE p.state = 'Texas'""",
        "gt": f"SELECT CAST(COALESCE(SUM(p.employee_count), 0) AS BIGINT) FROM {fqn}.plants p WHERE p.state = 'Texas'",
    },
    {
        "q": "How many equipment_feedback rows are for production lines at the EV Battery Innovation Center (join feedback to production_lines and match that plant)?",
        "sql": f"""SELECT CAST(COUNT(*) AS BIGINT) AS answer FROM {fqn}.equipment_feedback f JOIN {fqn}.production_lines pl ON f.production_line_id = pl.line_id JOIN {fqn}.plants p ON pl.plant_id = p.plant_id WHERE p.plant_name = 'EV Battery Innovation Center'""",
        "gt": f"SELECT CAST(COUNT(*) AS BIGINT) FROM {fqn}.equipment_feedback f JOIN {fqn}.production_lines pl ON f.production_line_id = pl.line_id JOIN {fqn}.plants p ON pl.plant_id = p.plant_id WHERE p.plant_name = 'EV Battery Innovation Center'",
    },
    {
        "q": "For plant P003 only and calendar year 2024, what is average OEE as a whole percent rounded to an integer (average oee_score times 100, then round)?",
        "sql": f"""SELECT CAST(ROUND(AVG(q.oee_score) * 100, 0) AS BIGINT) AS answer FROM {fqn}.quality_metrics_daily q WHERE q.plant_id = 'P003' AND YEAR(CAST(q.date AS DATE)) = 2024""",
        "gt": f"SELECT CAST(ROUND(AVG(q.oee_score) * 100, 0) AS BIGINT) FROM {fqn}.quality_metrics_daily q WHERE q.plant_id = 'P003' AND YEAR(CAST(q.date AS DATE)) = 2024",
    },
]
print(len(benchmarks_v1), "benchmarks (v2 harder suite)")
'''
    ),
    md(
        "## Verify ground truth in Spark",
        "",
        "Run each `gt` query once. Fix definitions before pushing to Genie if any fail.",
    ),
    code(
        '''
for i, b in enumerate(benchmarks_v1, 1):
    try:
        v = spark.sql(b["gt"]).collect()[0][0]
        print(f"OK Q{i}: {v}")
    except Exception as e:
        print(f"FAIL Q{i}: {e}")
'''
    ),
    md(
        "## Push benchmarks to Genie (update evaluation rail)",
        "",
        "Registers **BENCHMARK** curated questions on the **primary** space. If the data-rooms API errors, copy the printed Q→SQL into Genie manually.",
    ),
    code("push_benchmarks(benchmarks_v1, SID_PRIMARY, 'Manufacturing v1 → primary space')"),
    md(
        "## Suggested follow-ups in the Genie UI",
        "",
        "1. Open the space → add any failing or missing themes as **additional** curated examples (not only benchmarks).",
        "2. Ask one benchmark question in chat and confirm the SQL matches your intent.",
        "3. Continue to notebook **04** to explore freely, then **05**–**06** for skills and A/B testing.",
    ),
]

# --- 06 Compare Genie with evals vs without (step 6/9) ---
CELLS_06_COMPARE = [
    md(
        "# Step 6 — Compare Genie: with in-space evals vs without",
        "",
        "Runs the **same** benchmark questions against:",
        "",
        "- **`genie_space_id`** — business instructions **plus** sample questions and curated Q→SQL (and BENCHMARK rows from notebook **03**).",
        "- **`genie_space_id_configured_no_evals`** — **same** instructions, **no** sample/curated pairs (skills live in Genie Code; this space stays clean for A/B).",
        "",
        "Pass rates demonstrate why **in-space examples and eval rails** matter. Prerequisites: **01**, **02**, **03**.",
    ),
    md("## Serverless compute", "", "Use **Serverless**. Config uses **widgets** only."),
    md("## Configuration", "", "Load both space IDs from `workshop_config`."),
    code(
        '''
dbutils.widgets.text("catalog", "gm_ama_demos", "Catalog")
dbutils.widgets.text("schema", "genie_workshop_manufacturing", "Schema")

CATALOG = dbutils.widgets.get("catalog")
SCHEMA = dbutils.widgets.get("schema")
fqn = f"{CATALOG}.{SCHEMA}"

from databricks.sdk import WorkspaceClient
import requests, time, re
from pyspark.sql.types import StructType, StructField, IntegerType, StringType, DoubleType
from datetime import datetime

w = WorkspaceClient()
host = w.config.host.rstrip("/")
auth = {**w.config.authenticate(), "Content-Type": "application/json"}


def _cfg(key):
    rows = spark.sql(
        f"SELECT value FROM {fqn}.workshop_config WHERE key = '{key}'"
    ).collect()
    return rows[0]["value"] if rows else None


SID_WITH = _cfg("genie_space_id")
SID_NO = _cfg("genie_space_id_configured_no_evals")
if not SID_WITH:
    raise RuntimeError("Missing genie_space_id — run notebook 02.")
if not SID_NO:
    raise RuntimeError("Missing genie_space_id_configured_no_evals — run notebook 02.")
print("WITH examples:", SID_WITH)
print("WITHOUT examples:", SID_NO)

import html


def genie_ui_room_url(host: str, space_id: str) -> str:
    h = (host or "").rstrip("/")
    sid = str(space_id or "").strip()
    m = re.search(r"adb-(\\d+)\\.", h)
    o = m.group(1) if m else ""
    q = f"?o={o}" if o else ""
    return f"{h}/genie/rooms/{sid}{q}"


for _label, _sid in (
    ("WITH in-space examples", SID_WITH),
    ("WITHOUT in-space examples (instructions only)", SID_NO),
):
    _u = genie_ui_room_url(host, _sid)
    print(_label, "Genie UI URL:", _u)
    displayHTML(
        '<p><b>'
        + html.escape(_label)
        + '</b> &mdash; <a href="'
        + html.escape(_u, quote=True)
        + '" target="_blank" rel="noopener">Open in Genie</a></p>'
    )


def ask_genie(question, space_id, timeout=90):
    try:
        s = requests.post(
            f"{host}/api/2.0/genie/spaces/{space_id}/start-conversation",
            headers=auth,
            json={"content": question},
        )
        if s.status_code != 200:
            return None, f"HTTP {s.status_code}"
        d = s.json()
        cid, mid = d.get("conversation_id"), d.get("message_id")
        for _ in range(timeout // 3):
            time.sleep(3)
            p = requests.get(
                f"{host}/api/2.0/genie/spaces/{space_id}/conversations/{cid}/messages/{mid}",
                headers=auth,
            )
            if p.status_code != 200:
                continue
            msg = p.json()
            if msg.get("status") == "COMPLETED":
                for att in msg.get("attachments", []):
                    if att.get("query"):
                        aid = att.get("attachment_id") or att.get("id", "")
                        qr = requests.get(
                            f"{host}/api/2.0/genie/spaces/{space_id}/conversations/{cid}/messages/{mid}/query-result/{aid}",
                            headers=auth,
                        )
                        if qr.status_code != 200:
                            qr = requests.get(
                                f"{host}/api/2.0/genie/spaces/{space_id}/conversations/{cid}/messages/{mid}/query-result",
                                headers=auth,
                            )
                        if qr.status_code == 200:
                            arr = (
                                qr.json()
                                .get("statement_response", {})
                                .get("result", {})
                                .get("data_array", [])
                            )
                            if arr and arr[0]:
                                m = re.search(
                                    r"-?\\d+\\.?\\d*",
                                    str(arr[0][0]).replace(",", "").replace("$", ""),
                                )
                                if m:
                                    return round(float(m.group())), None
                return None, "No numeric value"
            if msg.get("status") in ("FAILED", "CANCELLED"):
                return None, msg.get("status")
        return None, "Timeout"
    except Exception as e:
        return None, str(e)[:80]


def run_benchmarks(benchmarks_list, space_id, label="Run"):
    results = []
    print(label)
    for i, b in enumerate(benchmarks_list, 1):
        try:
            gt = round(float(spark.sql(b["gt"]).collect()[0][0]))
        except Exception:
            gt = None
        gv, err = ask_genie(b["q"], space_id)
        if gv is not None and gt is not None and gt != 0:
            diff = abs(gv - gt) / abs(gt)
            st = "PASS" if diff < 0.05 else ("WARN" if diff < 0.15 else "FAIL")
        elif gv is None:
            st = f"FAIL {err or 'no answer'}"
        else:
            st = "PASS" if gv == gt else "FAIL"
        print(f"Q{i} {st} gt={gt} genie={gv}")
        results.append((i, b["q"][:60], float(gt) if gt is not None else None, float(gv) if gv is not None else None, st))
        time.sleep(1)
    passed = sum(1 for r in results if r[4] == "PASS")
    rate = passed / len(results) * 100 if results else 0
    print(f"Score: {passed}/{len(results)} ({rate:.0f}%)")
    return results, rate


benchmarks_v1 = [
    {
        "q": "How many distinct production lines had at least one defect_detected event in calendar year 2024?",
        "gt": f"SELECT CAST(COUNT(DISTINCT production_line_id) AS BIGINT) FROM {fqn}.production_events WHERE event_type = 'defect_detected' AND YEAR(CAST(event_date AS DATE)) = 2024",
    },
    {
        "q": "What is the sum of downtime_minutes from quality_metrics_daily for all rows in 2024 where the plant is in Michigan (join to plants by state)?",
        "gt": f"SELECT CAST(ROUND(SUM(q.downtime_minutes), 0) AS BIGINT) FROM {fqn}.quality_metrics_daily q JOIN {fqn}.plants p ON q.plant_id = p.plant_id WHERE p.state = 'Michigan' AND YEAR(CAST(q.date AS DATE)) = 2024",
    },
    {
        "q": "What is the total units_produced summed from quality_metrics_daily for January through March 2024 (Q1) only?",
        "gt": f"SELECT CAST(SUM(q.units_produced) AS BIGINT) FROM {fqn}.quality_metrics_daily q WHERE CAST(q.date AS DATE) >= DATE '2024-01-01' AND CAST(q.date AS DATE) < DATE '2024-04-01'",
    },
    {
        "q": "How many production lines had 500 or more unit_produced events in calendar year 2024?",
        "gt": f"SELECT CAST(COUNT(*) AS BIGINT) FROM ( SELECT production_line_id FROM {fqn}.production_events WHERE event_type = 'unit_produced' AND YEAR(CAST(event_date AS DATE)) = 2024 GROUP BY production_line_id HAVING COUNT(*) >= 500 ) t",
    },
    {
        "q": "How many safety incidents are both severity Critical and category Equipment Malfunction?",
        "gt": f"SELECT CAST(COUNT(*) AS BIGINT) FROM {fqn}.safety_incidents WHERE severity = 'Critical' AND category = 'Equipment Malfunction'",
    },
    {
        "q": "How many operators work at plants located in Michigan (use operators.plant_id joined to plants)?",
        "gt": f"SELECT CAST(COUNT(*) AS BIGINT) FROM {fqn}.operators o JOIN {fqn}.plants p ON o.plant_id = p.plant_id WHERE p.state = 'Michigan'",
    },
    {
        "q": "For calendar year 2024 quality_metrics_daily only, what is the overall defect rate in percent rounded to a whole number: 100 times the sum of defects_found divided by the sum of units_produced?",
        "gt": f"SELECT CAST(ROUND(100.0 * SUM(defects_found) / SUM(units_produced), 0) AS BIGINT) FROM {fqn}.quality_metrics_daily WHERE YEAR(CAST(date AS DATE)) = 2024",
    },
    {
        "q": "How many production events in 2024 have event_type inspection_passed?",
        "gt": f"SELECT CAST(COUNT(*) AS BIGINT) FROM {fqn}.production_events WHERE event_type = 'inspection_passed' AND YEAR(CAST(event_date AS DATE)) = 2024",
    },
    {
        "q": "How many quality_metrics_daily rows in 2024 have oee_score strictly below 0.70?",
        "gt": f"SELECT CAST(COUNT(*) AS BIGINT) FROM {fqn}.quality_metrics_daily WHERE YEAR(CAST(date AS DATE)) = 2024 AND oee_score < 0.70",
    },
    {
        "q": "What is the sum of employee_count for all plants in Texas?",
        "gt": f"SELECT CAST(COALESCE(SUM(p.employee_count), 0) AS BIGINT) FROM {fqn}.plants p WHERE p.state = 'Texas'",
    },
    {
        "q": "How many equipment_feedback rows are for production lines at the EV Battery Innovation Center (join feedback to production_lines and match that plant)?",
        "gt": f"SELECT CAST(COUNT(*) AS BIGINT) FROM {fqn}.equipment_feedback f JOIN {fqn}.production_lines pl ON f.production_line_id = pl.line_id JOIN {fqn}.plants p ON pl.plant_id = p.plant_id WHERE p.plant_name = 'EV Battery Innovation Center'",
    },
    {
        "q": "For plant P003 only and calendar year 2024, what is average OEE as a whole percent rounded to an integer (average oee_score times 100, then round)?",
        "gt": f"SELECT CAST(ROUND(AVG(q.oee_score) * 100, 0) AS BIGINT) FROM {fqn}.quality_metrics_daily q WHERE q.plant_id = 'P003' AND YEAR(CAST(q.date AS DATE)) = 2024",
    },
]
print(len(benchmarks_v1), "benchmarks loaded (v2 harder suite)")
'''
    ),
    md(
        "## Run A/B benchmark pass",
        "",
        "Same **v2** questions as notebook **03**; 5% relative tolerance when ground truth is non-zero. Expect the **without-examples** space to slip **before** the primary space on harder joins and ratios.",
    ),
    code(
        '''
results_with, rate_with = run_benchmarks(
    benchmarks_v1, SID_WITH, "=== WITH in-space examples (+ benchmarks from 03) ==="
)
results_no, rate_no = run_benchmarks(
    benchmarks_v1, SID_NO, "=== WITHOUT in-space examples (instructions only) ==="
)

schema = StructType(
    [
        StructField("benchmark_id", IntegerType()),
        StructField("question", StringType()),
        StructField("ground_truth", DoubleType()),
        StructField("genie_answer", DoubleType()),
        StructField("status", StringType()),
    ]
)
from pyspark.sql import functions as F

df_w = spark.createDataFrame(results_with, schema).withColumn("variant", F.lit("with_examples"))
df_n = spark.createDataFrame(results_no, schema).withColumn("variant", F.lit("no_examples"))
display(df_w.unionByName(df_n))

print(f"Pass rate WITH examples: {rate_with:.1f}%")
print(f"Pass rate WITHOUT examples: {rate_no:.1f}%")
'''
    ),
    md("## Save run history", "", "Appends to `genie_benchmark_runs` for notebook **09** (monitoring)."),
    code(
        '''
ts = datetime.now().isoformat()
sch = StructType(
    [
        StructField("benchmark_id", IntegerType()),
        StructField("question", StringType()),
        StructField("ground_truth", DoubleType()),
        StructField("genie_answer", DoubleType()),
        StructField("status", StringType()),
        StructField("run_timestamp", StringType()),
        StructField("pass_rate", DoubleType()),
        StructField("run_label", StringType()),
    ]
)
rows = []
rows += [(r[0], r[1], r[2], r[3], r[4], ts, rate_with, "manufacturing_v1_with_examples") for r in results_with]
rows += [(r[0], r[1], r[2], r[3], r[4], ts, rate_no, "manufacturing_v1_no_examples") for r in results_no]

tbl = f"{fqn}.genie_benchmark_runs"
try:
    spark.createDataFrame(rows, sch).write.mode("append").saveAsTable(tbl)
except Exception:
    spark.sql(f"DROP TABLE IF EXISTS {tbl}")
    spark.createDataFrame(rows, sch).write.saveAsTable(tbl)
print(f"Saved to {tbl}")
'''
    ),
]

# --- 04 talk with data (step 4/9) ---
CELLS_04 = [
    md(
        "# Step 4 — Talk with your manufacturing data",
        "",
        "After **02** (space + information) and **03** (evals pushed), explore Genie in the UI. Notebook **01** uses **seed 42**, so the **Reference SQL** cell below gives **reproducible ground truth** for your catalog/schema—compare Genie’s numbers and wording to those results.",
    ),
    md("## Serverless", "", "Use **Serverless** compute."),
    md(
        "## Configuration",
        "",
        "Use the **same** **Catalog** and **Schema** widgets as notebooks **01** and **02** (your tutorial path). The Genie **browser** link is **not** read from `workshop_config.space_url` (that can go stale); it is **computed** from this workspace’s **host** plus the **space id** in `workshop_config.value` for `genie_space_id` — pattern: `/genie/rooms/<space_id>?o=<workspace>` on Azure (`adb-<id>` in the hostname).",
    ),
    code(
        '''
import html
import re

from databricks.sdk import WorkspaceClient

dbutils.widgets.text("catalog", "gm_ama_demos", "Catalog")
dbutils.widgets.text("schema", "genie_workshop_manufacturing", "Schema")
CATALOG = dbutils.widgets.get("catalog")
SCHEMA = dbutils.widgets.get("schema")
fqn = f"{CATALOG}.{SCHEMA}"


def genie_ui_room_url(host: str, space_id: str) -> str:
    h = (host or "").rstrip("/")
    sid = str(space_id or "").strip()
    m = re.search(r"adb-(\\d+)\\.", h)
    o = m.group(1) if m else ""
    q = f"?o={o}" if o else ""
    return f"{h}/genie/rooms/{sid}{q}"


w = WorkspaceClient()
_host = w.config.host.rstrip("/")

cfg = spark.sql(
    f"SELECT value, space_name FROM {fqn}.workshop_config WHERE key = 'genie_space_id'"
).collect()
if not cfg:
    print("Run notebook 02 first — no genie_space_id in workshop_config.")
else:
    _sid = cfg[0]["value"]
    _name = cfg[0]["space_name"]
    _u = genie_ui_room_url(_host, _sid)
    print("Primary space id:", _sid)
    print("Primary Genie UI URL (computed):", _u)
    displayHTML(
        "<p>"
        + html.escape(str(_name))
        + ' &mdash; <a href="'
        + html.escape(_u, quote=True)
        + '" target="_blank" rel="noopener">Open in Genie</a></p>'
    )
'''
    ),
    md(
        "## Quality and OEE — try in Genie, then compare",
        "",
        "1. **What is the average OEE by plant for 2024?**",
        "   - **Expected answer:** One row per plant with **average OEE %** = `AVG(oee_score) * 100` over `quality_metrics_daily` rows where `YEAR(date) = 2024`, joined to `plants` for the name. Ordering may vary; values should match the reference table below.",
        "",
        "2. **Which production lines have the highest defect rates in 2024?**",
        "   - **Expected answer:** Defect rate **%** = `COUNT(defect_detected) / COUNT(unit_produced) * 100` on `production_events` in 2024, grouped by line (join `production_lines`). Highest rates appear at the **top** when sorted descending.",
        "",
        "3. **Show first pass yield trend by month for 2024.**",
        "   - **Expected answer:** One row per **month** with **avg FPY %** = `AVG(first_pass_yield) * 100` from `quality_metrics_daily` where `YEAR(date)=2024`, e.g. `DATE_TRUNC('month', date)`.",
    ),
    md(
        "## Production and downtime — try in Genie, then compare",
        "",
        "1. **Compare total downtime minutes across plants.**",
        "   - **Expected answer:** **Sum** of `downtime_minutes` from `quality_metrics_daily`, grouped by plant (join `plants`).",
        "",
        "2. **How many unit_produced events occurred in Q1 2024?**",
        "   - **Expected answer:** A **single count** of rows in `production_events` where `event_type = 'unit_produced'` and `event_date` is in **2024-01-01** through **2024-03-31** (inclusive).",
    ),
    md(
        "## Safety — try in Genie, then compare",
        "",
        "1. **List critical safety incidents.**",
        "   - **Expected answer:** Rows from `safety_incidents` where `severity = 'Critical'`, typically ordered by `incident_date` descending.",
        "",
        "2. **How many incidents by severity?**",
        "   - **Expected answer:** **Counts** grouped by `severity` (values include Low, Medium, High, Critical per notebook 01).",
    ),
    md(
        "## Reference SQL — ground truth for the prompts above",
        "",
        "Run this cell after **01_setup_data** on the **same** catalog/schema. Use the outputs as the **expected answers** when validating Genie.",
    ),
    code(
        '''
print("=== 1. Average OEE % by plant (2024) ===")
display(
    spark.sql(
        f"""
SELECT p.plant_name, ROUND(AVG(q.oee_score) * 100, 2) AS avg_oee_pct
FROM {fqn}.quality_metrics_daily q
JOIN {fqn}.plants p ON q.plant_id = p.plant_id
WHERE YEAR(q.date) = 2024
GROUP BY p.plant_name
ORDER BY avg_oee_pct DESC
"""
    )
)

print("=== 2. Defect rate % by production line (2024, top 15) ===")
display(
    spark.sql(
        f"""
SELECT
  pl.line_name,
  ROUND(
    SUM(CASE WHEN pe.event_type = 'defect_detected' THEN 1 ELSE 0 END) * 100.0
    / NULLIF(SUM(CASE WHEN pe.event_type = 'unit_produced' THEN 1 ELSE 0 END), 0),
    2
  ) AS defect_rate_pct
FROM {fqn}.production_events pe
JOIN {fqn}.production_lines pl ON pe.production_line_id = pl.line_id
WHERE YEAR(pe.event_date) = 2024
GROUP BY pl.line_id, pl.line_name
ORDER BY defect_rate_pct DESC
LIMIT 15
"""
    )
)

print("=== 3. First pass yield % by month (2024) ===")
display(
    spark.sql(
        f"""
SELECT
  DATE_TRUNC('month', q.date) AS month,
  ROUND(AVG(q.first_pass_yield) * 100, 2) AS avg_fpy_pct
FROM {fqn}.quality_metrics_daily q
WHERE YEAR(q.date) = 2024
GROUP BY DATE_TRUNC('month', q.date)
ORDER BY month
"""
    )
)

print("=== 4. Total downtime minutes by plant ===")
display(
    spark.sql(
        f"""
SELECT p.plant_name, ROUND(SUM(q.downtime_minutes), 2) AS total_downtime_minutes
FROM {fqn}.quality_metrics_daily q
JOIN {fqn}.plants p ON q.plant_id = p.plant_id
GROUP BY p.plant_name
ORDER BY total_downtime_minutes DESC
"""
    )
)

print("=== 5. unit_produced events in Q1 2024 ===")
display(
    spark.sql(
        f"""
SELECT CAST(COUNT(*) AS BIGINT) AS unit_produced_events_q1_2024
FROM {fqn}.production_events
WHERE event_type = 'unit_produced'
  AND event_date >= DATE('2024-01-01')
  AND event_date < DATE('2024-04-01')
"""
    )
)

print("=== 6. Critical safety incidents ===")
display(
    spark.sql(
        f"""
SELECT incident_id, incident_date, production_line_id, severity, description
FROM {fqn}.safety_incidents
WHERE severity = 'Critical'
ORDER BY incident_date DESC
"""
    )
)

print("=== 7. Incident counts by severity ===")
display(
    spark.sql(
        f"""
SELECT severity, COUNT(*) AS incident_count
FROM {fqn}.safety_incidents
GROUP BY severity
ORDER BY severity
"""
    )
)
'''
    ),
]

# --- 05 Genie Code + skills; no in-space evals space (step 5/9) ---
CELLS_05 = [
    md(
        "# Step 5 — Genie Code, skills, and the no-eval Genie space",
        "",
        "**Genie (SQL)** space **`genie_space_id_configured_no_evals`** (from notebook **02**) has the **same business instructions** as the primary space but **no** sample questions or curated Q→SQL — it models “instructions only,” while **Genie Code** picks up **skills** from the workspace.",
        "",
        "Install the workshop skill so Code understands OEE, FPY, joins, and naming. Then use Code against your catalog or use the **no-eval** Genie space for SQL-only A/B (notebook **06**).",
        "",
        "Skill source in repo: `skill/gm-genie-manufacturing-context/SKILL.md`.",
    ),
    md("## Serverless", "", "Use **Serverless**."),
    md(
        "## Open your Genie spaces (browser)",
        "",
        "Same tables and text instructions as primary for **`genie_space_id`**; the no-eval space (**`genie_space_id_configured_no_evals`**) has no in-space curated examples. Links below use **space id** + current **workspace host** (same rule as notebook **02**).",
    ),
    code(
        '''
import html
import re

from databricks.sdk import WorkspaceClient

dbutils.widgets.text("catalog", "gm_ama_demos", "Catalog")
dbutils.widgets.text("schema", "genie_workshop_manufacturing", "Schema")
CATALOG = dbutils.widgets.get("catalog")
SCHEMA = dbutils.widgets.get("schema")
fqn = f"{CATALOG}.{SCHEMA}"


def genie_ui_room_url(host: str, space_id: str) -> str:
    h = (host or "").rstrip("/")
    sid = str(space_id or "").strip()
    m = re.search(r"adb-(\\d+)\\.", h)
    o = m.group(1) if m else ""
    q = f"?o={o}" if o else ""
    return f"{h}/genie/rooms/{sid}{q}"


w = WorkspaceClient()
_host = w.config.host.rstrip("/")

rows = spark.sql(
    f"""SELECT key, value, space_name FROM {fqn}.workshop_config
        WHERE key IN ('genie_space_id_configured_no_evals', 'genie_space_id')
        ORDER BY key"""
).collect()
for r in rows:
    _u = genie_ui_room_url(_host, r["value"])
    print(r["key"], "->", _u)
    displayHTML(
        "<p><b>"
        + html.escape(str(r["key"]))
        + "</b> &mdash; "
        + html.escape(str(r["space_name"]))
        + ' &mdash; <a href="'
        + html.escape(_u, quote=True)
        + '" target="_blank" rel="noopener">Open in Genie</a><br/><code style="font-size:11px">'
        + html.escape(_u)
        + "</code></p>"
    )
'''
    ),
    md(
        "## Install skills (Genie Code)",
        "",
        "Copy `skill/gm-genie-manufacturing-context/` into your user or repo **`.assistant/skills`** path (see current Genie Code docs). Skills are **not** stored inside the Genie SQL space JSON.",
    ),
    md("## Sample `SKILL.md` excerpt", "", "Paste into the skill file or use the bundled copy in the repo."),
    code(
        '''
skill_md = """
---
name: gm-genie-manufacturing-context
description: Manufacturing quality metrics and joins for Genie Code
---

# GM manufacturing context

- OEE: `quality_metrics_daily.oee_score` is 0 to 1 (multiply by 100 for percent).
- FPY: `first_pass_yield` same scale.
- Defect rate: COUNT defect_detected / COUNT unit_produced on production_events.
- Join events to lines: production_events.production_line_id = production_lines.line_id
- Join lines to plants: production_lines.plant_id = plants.plant_id
"""
print(skill_md)
'''
    ),
]

# --- 07 security (step 7/9) — Vizient-style proof: VIN-like column + restricted view + Genie on view only ---
CELLS_07_SECURITY = [
    md(
        "# Step 7 — Security and governance (manufacturing)",
        "",
        "**Goal:** Prove Genie does **not** bypass Unity Catalog — same masking as SQL.",
        "",
        "Notebook **01** adds **`unit_serial_vin`** (17-character unit traceability id, VIN-style) on **`production_events`**. Here we:",
        "",
        "1. Show **non-null VINs** on the **base table** (sensitive source).",
        "2. Create **`production_events_restricted`**: `unit_serial_vin` is **NULL** unless `is_member('admin_group')` (common UC pattern: sensitive column visible only to an admin group).",
        "3. Compare **direct SQL** on base table vs view.",
        "4. Create a **Genie Data Room** attached **only** to the restricted view and ask Genie for VINs — results should match the view (**masked** for typical workshop users).",
        "",
        "**Prerequisite:** Re-run **01** after the VIN column was added so the column exists.",
    ),
    md("## Serverless", "", "Use **Serverless**."),
    md("## Configuration", "", "Same **catalog** / **schema** widgets as the rest of the workshop."),
    code(
        '''
dbutils.widgets.text("catalog", "gm_ama_demos", "Catalog")
dbutils.widgets.text("schema", "genie_workshop_manufacturing", "Schema")
CATALOG = dbutils.widgets.get("catalog")
SCHEMA = dbutils.widgets.get("schema")
fqn = f"{CATALOG}.{SCHEMA}"
'''
    ),
    md(
        "## Step 1 — Sensitive data on the base table",
        "",
        "Sample rows should show **populated** `unit_serial_vin` values (seeded in notebook **01**).",
    ),
    code(
        '''
display(
    spark.sql(
        f"""
SELECT event_id, event_type, event_date, part_number, unit_serial_vin
FROM {fqn}.production_events
WHERE unit_serial_vin IS NOT NULL
LIMIT 8
"""
    )
)
'''
    ),
    md(
        "## Step 2 — Who has access to `production_events`?",
        "",
        "Review grants before sharing any Genie space. Genie can only return data the backing tables/views allow.",
    ),
    code('display(spark.sql(f"SHOW GRANTS ON TABLE {fqn}.production_events"))'),
    md(
        "## Step 3 — Audit log sample (Genie-related)",
        "",
        "May require elevated workspace permissions; failures are expected in some sandboxes.",
    ),
    code(
        '''
try:
    display(
        spark.sql(
            """
        SELECT event_date, user_identity.email AS email, action_name
        FROM system.access.audit
        WHERE LOWER(CAST(action_name AS STRING)) LIKE '%genie%'
          AND event_date >= current_date() - INTERVAL 7 DAYS
        ORDER BY event_date DESC
        LIMIT 20
    """
        )
    )
except Exception as e:
    print("Audit query not available:", str(e)[:200])
'''
    ),
    md(
        "## Step 4 — Restricted view (mask `unit_serial_vin`)",
        "",
        "Non-members of **`admin_group`** see **NULL** for `unit_serial_vin`. Admins see the real value.",
        "",
        "> Workshop tip: If you **are** in `admin_group`, you will see VINs in both the proof query and Genie — use a user **outside** that group to demo masking, or temporarily validate with `SELECT is_member('admin_group')`.",
    ),
    code(
        '''
spark.sql(
    f"""
CREATE OR REPLACE VIEW {fqn}.production_events_restricted AS
SELECT
  event_id,
  event_type,
  event_date,
  event_timestamp,
  production_line_id,
  operator_id,
  part_number,
  CASE WHEN is_member('admin_group') THEN unit_serial_vin ELSE CAST(NULL AS STRING) END AS unit_serial_vin,
  defect_code
FROM {fqn}.production_events
"""
)
print("Created view:", f"{fqn}.production_events_restricted")
'''
    ),
    md(
        "## Step 5 — Direct SQL: base table vs restricted view",
        "",
        "Same user, two objects: base table shows VINs; view should show **NULL** in `unit_serial_vin` when `is_member('admin_group')` is false.",
    ),
    code(
        '''
print("--- Base table (sensitive source) ---")
display(
    spark.sql(
        f"SELECT event_id, unit_serial_vin FROM {fqn}.production_events ORDER BY event_id LIMIT 5"
    )
)
print("--- Restricted view (what broad Genie users should see) ---")
display(
    spark.sql(
        f"SELECT event_id, unit_serial_vin FROM {fqn}.production_events_restricted ORDER BY event_id LIMIT 5"
    )
)
row = spark.sql(f"SELECT unit_serial_vin FROM {fqn}.production_events_restricted LIMIT 1").collect()
if row and row[0][0] is None:
    print("Masking check: first row unit_serial_vin is NULL (expected for non-admin_group).")
elif row:
    print("You appear to have admin_group (or equivalent) — VIN visible; use a non-admin principal to demo masking.")
'''
    ),
    md(
        "## Step 6 — Genie space on the restricted view only",
        "",
        "Creates a small **Data Room / Genie** space whose **only** table is **`production_events_restricted`**, so Genie cannot read the base table directly.",
        "",
        "If the API returns an error, create the space manually in the UI and attach **only** this view.",
    ),
    code(
        '''
import re
import time

import requests
from databricks.sdk import WorkspaceClient

MASKED_SPACE_ID = None
w = WorkspaceClient()
host = w.config.host.rstrip("/")
api_headers = {**w.config.authenticate(), "Content-Type": "application/json"}

warehouses = list(w.warehouses.list())
warehouse_id = None
for wh in warehouses:
    state = str(wh.state).upper() if wh.state else ""
    if state in ("RUNNING", "STARTING") or getattr(wh, "enable_serverless_compute", False):
        warehouse_id = wh.id
        break
if not warehouse_id and warehouses:
    warehouse_id = warehouses[0].id

MASKED_SPACE_ID = None
if not warehouse_id:
    print("No SQL warehouse found — create the Genie space manually and attach", f"{fqn}.production_events_restricted")
else:
    payload = {
        "display_name": "GM Workshop — Security demo (masked VIN)",
        "description": "Genie sees only production_events_restricted; unit_serial_vin masked for non-admins",
        "warehouse_id": warehouse_id,
        "table_identifiers": [f"{fqn}.production_events_restricted"],
        "run_as_type": "VIEWER",
    }
    resp = requests.post(f"{host}/api/2.0/data-rooms/", headers=api_headers, json=payload)
    if resp.status_code in (200, 201):
        body = resp.json()
        MASKED_SPACE_ID = body.get("space_id") or body.get("id")
        print("Created masked Genie space:", MASKED_SPACE_ID)
        m = re.search(r"adb-(\\d+)\\.", host)
        o = m.group(1) if m else ""
        q = f"?o={o}" if o else ""
        print("Open:", f"{host}/genie/rooms/{MASKED_SPACE_ID}{q}")
    else:
        print("Data Room API returned", resp.status_code, resp.text[:400])
        print("Manual: New Genie space → add only table", f"{fqn}.production_events_restricted")
'''
    ),
    md(
        "## Step 7 — Ask Genie for VINs and verify masking",
        "",
        "If **`MASKED_SPACE_ID`** was created, we ask Genie to return VINs. For **non-admin** users, `unit_serial_vin` should be **NULL** in the result — proving Genie respects the view.",
    ),
    code(
        '''
def _ask_genie_show_vin_masking(space_id, question):
    if not space_id:
        print("No space id — skip (complete Step 6 or create space in UI).")
        return
    print("Asking:", question)
    start = requests.post(
        f"{host}/api/2.0/genie/spaces/{space_id}/start-conversation",
        headers=api_headers,
        json={"content": question},
    )
    if start.status_code != 200:
        print("start-conversation failed:", start.status_code, start.text[:300])
        return
    d = start.json()
    cid, mid = d.get("conversation_id"), d.get("message_id")
    for _ in range(30):
        time.sleep(3)
        poll = requests.get(
            f"{host}/api/2.0/genie/spaces/{space_id}/conversations/{cid}/messages/{mid}",
            headers=api_headers,
        )
        if poll.status_code != 200:
            continue
        msg = poll.json()
        st = msg.get("status", "")
        if st == "COMPLETED":
            for att in msg.get("attachments", []):
                aid = att.get("attachment_id") or att.get("id")
                if not att.get("query") or not aid:
                    continue
                qr = requests.get(
                    f"{host}/api/2.0/genie/spaces/{space_id}/conversations/{cid}/messages/{mid}/query-result/{aid}",
                    headers=api_headers,
                )
                if qr.status_code != 200:
                    continue
                j = qr.json()
                arr = j.get("statement_response", {}).get("result", {}).get("data_array", [])
                cols = j.get("statement_response", {}).get("manifest", {}).get("schema", {}).get("columns", [])
                names = [c.get("name", "") for c in cols]
                print("Columns:", names)
                for i, row in enumerate(arr[:8]):
                    print(f"Row {i+1}:", row)
                idx = [i for i, n in enumerate(names) if n and n.lower().replace("_", "") == "unitserialvin"]
                if not idx:
                    idx = [i for i, n in enumerate(names) if "vin" in n.lower() or "serial" in n.lower()]
                if idx and arr:
                    v = arr[0][idx[0]] if idx[0] < len(arr[0]) else None
                    if v is None or v == "":
                        print("MASKING VERIFIED via Genie: unit_serial_vin is null/empty in query result (non-admin view).")
                    else:
                        print("VIN visible in Genie result — if demoing masking, run as a user not in admin_group.")
                return
            print("Genie completed but no query attachment found.")
            return
        if st in ("FAILED", "CANCELLED"):
            print("Genie status:", st)
            return
    print("Timeout waiting for Genie.")


try:
    _ask_genie_show_vin_masking(
        MASKED_SPACE_ID,
        "Show event_id, event_type, and unit_serial_vin for 8 production events from 2024, newest first.",
    )
except NameError:
    print("Run the previous cell first to set MASKED_SPACE_ID / host / api_headers.")
except Exception as e:
    print("Genie check error:", str(e)[:200])
'''
    ),
    md(
        "## Done — what you proved",
        "",
        "| Check | Meaning |",
        "|---|---|",
        "| Base `production_events` | VINs exist (sensitive source). |",
        "| `production_events_restricted` | Same rows, `unit_serial_vin` masked unless admin. |",
        "| Genie on **view only** | Answers match UC — **no bypass** of column masks. |",
        "",
        "**Cleanup:** Delete the **GM Workshop — Security demo** Genie space in the UI when finished if you do not want an extra space in the workspace.",
    ),
]

# --- 08 deployment strategies (step 8/9) ---
CELLS_08_DEPLOY = [
    md(
        "# Step 8 — Deployment strategies and practical wiring",
        "",
        "**Patterns:** (1) **AI Playground** for rapid demos, (2) **Databricks App** + Genie API for a packaged UI, (3) **Jobs** to refresh data while Genie reads current tables.",
        "",
        "**Best practices:** store **`GENIE_SPACE_ID`** in app secrets or job parameters — not in source control; use **separate spaces** per environment (dev/stage/prod) with the same instruction template; pin **warehouse** capacity for demos; document **who** can edit curated SQL in Genie.",
    ),
    md("## Serverless", "", "Use **Serverless** for notebooks; Apps and Jobs use workspace defaults you choose."),
    md(
        "## Workspace links + Genie space ID",
        "",
        "Run this cell **first** before Options A–C. Links use **`displayHTML`** so they are **clickable** in the notebook (plain `print` URLs often are not).",
        "",
        "On **Azure** (`adb-*` hostnames), workspace deep links need **`?o=<workspace_id>`** (same rule as Genie). Non-Azure workspaces omit `o` when the host does not match `adb-<digits>.`.",
        "",
        "If a Playground link 404s in your tenant, use the **hash-route** fallback or open **Playground** from the left sidebar (**Machine learning**).",
    ),
    code(
        '''
import html
import re

from databricks.sdk import WorkspaceClient

dbutils.widgets.text("catalog", "gm_ama_demos", "Catalog")
dbutils.widgets.text("schema", "genie_workshop_manufacturing", "Schema")
CATALOG = dbutils.widgets.get("catalog")
SCHEMA = dbutils.widgets.get("schema")

w = WorkspaceClient()
host_url = w.config.host.rstrip("/")


def _azure_workspace_o(host: str) -> str:
    m = re.search(r"adb-(\\d+)\\.", host or "")
    return m.group(1) if m else ""


def workspace_deeplink(host: str, path: str) -> str:
    # path must start with / e.g. /ml/playground
    h = (host or "").rstrip("/")
    p = path if path.startswith("/") else "/" + path
    base = h + p
    oid = _azure_workspace_o(h)
    if not oid:
        return base
    sep = "&" if "?" in base else "?"
    return f"{base}{sep}o={oid}"


def genie_ui_room_url(host: str, space_id: str) -> str:
    h = (host or "").rstrip("/")
    sid = str(space_id or "").strip()
    return workspace_deeplink(h, f"/genie/rooms/{sid}")


cfg = spark.sql(
    f"SELECT value FROM {CATALOG}.{SCHEMA}.workshop_config WHERE key = 'genie_space_id'"
).collect()
if not cfg:
    raise RuntimeError("Missing genie_space_id — run notebook 02.")
GENIE_SPACE_ID = cfg[0]["value"]
UI_URL = genie_ui_room_url(host_url, GENIE_SPACE_ID)

pg_ai = workspace_deeplink(host_url, "/ml/ai-playground")
pg_ml = workspace_deeplink(host_url, "/ml/playground")
_oid = _azure_workspace_o(host_url)
pg_hash = (
    f"{host_url}/?o={_oid}#/ml/playground"
    if _oid
    else f"{host_url}/#/ml/playground"
)
jobs_url = workspace_deeplink(host_url, "/jobs")
apps_url = workspace_deeplink(host_url, "/compute/apps")

print("GENIE_SPACE_ID:", GENIE_SPACE_ID)
print("Primary Genie UI:", UI_URL)


def _a(href: str, label: str) -> str:
    return (
        '<li style="margin:6px 0"><a href="'
        + html.escape(href, quote=True)
        + '" target="_blank" rel="noopener noreferrer">'
        + html.escape(label)
        + "</a></li>"
    )


_id_show = html.escape(str(GENIE_SPACE_ID))
_html = (
    '<div style="font-family:system-ui,Segoe UI,sans-serif;line-height:1.5;max-width:720px">'
    "<p><b>Clickable workspace links</b></p>"
    '<ul style="padding-left:1.2rem">'
    + _a(UI_URL, "Primary Genie space (SQL)")
    + _a(pg_ai, "AI Playground — /ml/ai-playground")
    + _a(pg_ml, "AI Playground — /ml/playground (legacy path)")
    + _a(pg_hash, "AI Playground — hash route fallback (?o=…#/ml/playground)")
    + _a(jobs_url, "Jobs")
    + _a(apps_url, "Compute → Apps (deploy Databricks App)")
    + "</ul>"
    '<p style="margin-top:12px;color:#555;font-size:13px">'
    "Copy space ID for Playground <b>Genie</b> tool:</p>"
    '<p style="font-family:monospace;font-size:14px;background:#f5f5f5;padding:8px;border-radius:6px">'
    + _id_show
    + "</p></div>"
)
displayHTML(_html)
'''
    ),
    md(
        "## Option A — Playground / Agent Builder",
        "",
        "1. Open **AI Playground** using a **clickable link** above (try **ai-playground** first).",
        "2. Add **Tool** → **Genie** → paste **`GENIE_SPACE_ID`** from the gray box.",
        "3. Ask: *What is average OEE by plant for 2024?*",
        "4. When stable, export or wire an App as needed.",
    ),
    code(
        '''
print("Sample Playground question: What is average OEE by plant for 2024?")
'''
    ),
    md(
        "## Option B — Databricks App (`app/`)",
        "",
        "Use **Compute → Apps** from the **clickable links** cell above. Sync `app/app.py`, `app/app.yaml`, `requirements.txt`. Set **`GENIE_SPACE_ID`** in **App environment** or a **secret scope** reference inside `app.yaml` (do not commit real IDs).",
        "",
        "Run the **Workspace links** cell before the next cell so **`GENIE_SPACE_ID`** is defined.",
    ),
    code(
        '''
# Practical: print lines you would place under env: in app.yaml (replace with secret reference in production).
print("app.yaml env example:")
print(f"  GENIE_SPACE_ID: '{GENIE_SPACE_ID}'  # use {{secrets/scope/key}} in real deployments")
'''
    ),
    md(
        "## Option C — Job + Genie",
        "",
        "Open **Jobs** from the **clickable links** cell above. Schedule **01** (or incremental loaders) as a Job; Genie spaces read **live** tables. Keep **benchmark** suite (notebook **03** / **06**) on a schedule if you regress Genie after model or instruction changes.",
    ),
    code(
        '''
# Example job parameter JSON fragment (documentation only):
job_params_example = {
    "catalog": CATALOG,
    "schema": SCHEMA,
    "notebook": "01_setup_data",
}
print(job_params_example)
'''
    ),
]

# --- 09 monitoring (step 9/9) ---
CELLS_09_MON = [
    md(
        "# Step 9 — Monitoring and observability (end-to-end)",
        "",
        "Review **benchmark history** from notebook **06**. Optionally sample **query history** for Genie-related SQL (permissions vary).",
    ),
    md("## Serverless", "", "Use **Serverless**."),
    md("## Configuration"),
    code(
        '''
dbutils.widgets.text("catalog", "gm_ama_demos", "Catalog")
dbutils.widgets.text("schema", "genie_workshop_manufacturing", "Schema")
CATALOG = dbutils.widgets.get("catalog")
SCHEMA = dbutils.widgets.get("schema")
fqn = f"{CATALOG}.{SCHEMA}"
'''
    ),
    md("## Benchmark run history"),
    code(
        '''
try:
    display(spark.sql(f"SELECT * FROM {fqn}.genie_benchmark_runs ORDER BY run_timestamp DESC LIMIT 50"))
except Exception as e:
    print("Run notebook 06 first or table missing:", e)
'''
    ),
    md("## Query history sample", "", "Best-effort; may be empty."),
    code(
        '''
try:
    display(
        spark.sql(
            """
        SELECT start_time, statement_text
        FROM system.query.history
        WHERE statement_text ILIKE '%genie%' OR statement_text ILIKE '%quality_metrics%'
        ORDER BY start_time DESC
        LIMIT 20
    """
        )
    )
except Exception as e:
    print("system.query.history not available:", str(e)[:150])
'''
    ),
]


def write_nb(path, name, cells):
    path.write_text(json.dumps(nb(name, cells), indent=1))
    print("Wrote", path)


def main():
    NB.mkdir(parents=True, exist_ok=True)
    write_nb(NB / "03_genie_evals_benchmarks.ipynb", "03_genie_evals_benchmarks", CELLS_03)
    write_nb(NB / "04_talk_with_data.ipynb", "04_talk_with_data", CELLS_04)
    write_nb(NB / "05_genie_code_skills.ipynb", "05_genie_code_skills", CELLS_05)
    write_nb(NB / "06_compare_genie_spaces.ipynb", "06_compare_genie_spaces", CELLS_06_COMPARE)
    write_nb(NB / "07_security_governance.ipynb", "07_security_governance", CELLS_07_SECURITY)
    write_nb(NB / "08_deployment_best_practices.ipynb", "08_deployment_best_practices", CELLS_08_DEPLOY)
    write_nb(NB / "09_monitoring_observability.ipynb", "09_monitoring_observability", CELLS_09_MON)

    app_dst = ROOT / "app"
    if VIZ_APP.is_dir():
        app_dst.mkdir(exist_ok=True)
        for f in ("app.py", "app.yaml", "requirements.txt"):
            src = VIZ_APP / f
            if src.is_file():
                shutil.copy2(src, app_dst / f)
        # Patch app.py for manufacturing
        p = app_dst / "app.py"
        t = p.read_text()
        t = t.replace("Vizient Supply Chain Analyzer", "GM Manufacturing Genie")
        t = t.replace(
            "Ask questions about spend, suppliers, contracts, and backorders in plain English.",
            "Ask questions about OEE, quality, production events, and safety in plain English.",
        )
        p.write_text(t)
        y = app_dst / "app.yaml"
        if y.exists():
            y.write_text(
                y.read_text().replace("vizient-supply-chain", "gm-manufacturing-genie")
            )
        print("Copied app from Vizient template")
    else:
        print("Vizient app not found at", VIZ_APP, "skip app copy")


if __name__ == "__main__":
    main()
