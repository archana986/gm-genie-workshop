---
name: manufacturing-analytics
description: Manufacturing quality domain knowledge + Genie space best practices. Use this skill when building Genie spaces, writing manufacturing analytics, or creating evaluation benchmarks.
---

# Manufacturing Analytics

## Part 1 — Manufacturing Domain Knowledge

### Key Metrics

- **OEE (Overall Equipment Effectiveness):** Measures productive time vs total available time. Typically stored as a 0-1 decimal — multiply by 100 for percent. Industry benchmarks: 85%+ world-class, 75%+ acceptable, <60% needs attention.
- **First Pass Yield (FPY):** Percentage of units passing quality inspection on the first attempt without rework. Same 0-1 scale as OEE.
- **Defect Rate:** Number of defect events divided by number of units produced, expressed as a percentage. Usually calculated per production line over a time window. Formula: `COUNT(defect_detected) / COUNT(unit_produced) * 100`.
- **Scrap Rate:** Scrapped units divided by total units produced as a percentage. Scrap is waste — defects that cannot be reworked. Formula: `scrap_count / units_produced * 100`. **Important:** Scrap rate is a ratio, not a count. When someone asks "what is the scrap rate," compute the ratio from `quality_metrics_daily`, not a count of scrap events.
- **Downtime:** Minutes or hours a production line is not running. Tracked daily per line. High downtime = lost capacity. Convert to hours: `downtime_minutes / 60`.
- **Mean Time Between Failures (MTBF):** Average operating time between equipment breakdowns.

### Typical Manufacturing Data Model

- **Plants/Sites** — One row per manufacturing facility. Key columns: plant ID, name, city, state, employee count, annual revenue.
- **Production Lines** — One row per line. Types: assembly, paint, stamping, EV battery, powertrain. Each line belongs to a plant. Status can be Active or Maintenance. **Important:** `status` is a current snapshot attribute, NOT time-varying. Do NOT filter `production_lines.status` by date — it reflects the line's current state regardless of when you query.
- **Operators** — One row per shop-floor worker. Shift (Morning/Afternoon/Night), certification type, home plant.
- **Production Events** — Event-level grain. Each row is one event: unit_produced, defect_detected, inspection_passed, downtime_start, scrap, rework_completed. Linked to a production line and operator.
- **Quality Metrics (Daily)** — One row per line per day. Rolled-up metrics: OEE score, first pass yield, downtime minutes, defects found, scrap count, units produced.
- **Safety Incidents** — One row per incident. Severity (Low/Medium/High/Critical), category (Ergonomic, Chemical, Equipment Malfunction, Slip/Trip/Fall, Electrical, Fire Hazard), root cause, corrective action.
- **Equipment Feedback** — Operator comments on equipment condition. Linked to a production line and operator.

### Common Join Paths

- Events → Lines → Plants (event grain up to plant level)
- Quality Metrics → Lines → Plants (daily grain up to plant level)
- Events → Operators (who was working when the event happened)
- Safety → Lines → Plants (where did the incident occur)
- Feedback → Lines → Plants (which equipment at which plant)
- Feedback → Operators (who submitted the feedback)

### Event Type Conventions

Production events typically use an `event_type` column with values:
`unit_produced`, `defect_detected`, `inspection_passed`, `downtime_start`, `scrap`, `rework_completed`

The distribution is weighted — `unit_produced` is the most common (~40%), followed by `inspection_passed` (~20%), with defects, downtime, scrap, and rework each around 10%.

### Date Handling

- Daily metrics often use a column named `date` (not `metric_date` or `report_date`)
- Event tables have both `event_date` (DATE type) and `event_timestamp` (TIMESTAMP)
- Filter by year: `YEAR(date) = 2024` or `date BETWEEN '2024-01-01' AND '2024-12-31'`
- Quarter filtering: Q1 = Jan-Mar, Q2 = Apr-Jun, Q3 = Jul-Sep, Q4 = Oct-Dec

### Sensitive Columns

- VIN / serial numbers (e.g., `unit_serial_vin`) are PII-adjacent — use views with column masking for broad audiences
- Employee names may need masking depending on governance policies
- Use Unity Catalog `CASE WHEN is_member('admin_group')` pattern for column masking

### Analysis Patterns

**OEE Analysis:**
1. Average OEE by plant (join quality metrics → lines → plants)
2. Monthly OEE trend (GROUP BY MONTH(date))
3. Compare to 85% target — flag plants below threshold

**Defect Analysis:**
1. Overall defect rate = COUNT(defect_detected) / COUNT(unit_produced) * 100
2. Top N lines by defect rate (subquery with HAVING)
3. Monthly defect rate trend

**Shift-Based Analysis:**
1. Join `production_events` to `operators` by `operator_id` to get the `shift` column — operators have the shift, events do not
2. Aggregate defects or production counts by shift
3. Compare shift performance for quality and throughput
4. For "best quality" shift: count defect_detected events per shift and find the MIN (fewest defects = best quality)

**Safety Analysis:**
1. Incident count by severity
2. Incident count by category
3. Monthly incident trend
4. Root cause distribution

---

## Part 2 — Genie Space Best Practices

### What Makes a Good Genie SQL Space

A well-configured Genie space has 6 components. Each component builds on the previous — skip one and answer quality drops.

### 1. SQL Instructions (required)

The most important component. These are free-text instructions that tell Genie how to query your data.

**What to include:**
- Metric definitions with exact formulas (e.g., "OEE is oee_score * 100, stored as 0-1")
- Join paths between tables (e.g., "Join production_events.production_line_id to production_lines.line_id")
- Column naming gotchas (e.g., "The date column is `date`, not `metric_date`")
- Scale conventions (e.g., "oee_score and first_pass_yield are 0-1 — always multiply by 100 for display")
- Sensitive column warnings (e.g., "unit_serial_vin is sensitive — use the restricted view for non-admin users")
- Available SQL functions (e.g., "compute_defect_rate(line_id, start_date, end_date) returns defect % for a line")

**What to avoid:**
- Long-form text paragraphs (Genie's context window is limited — keep instructions concise)
- Duplicate information already in table/column comments
- Business context that doesn't help with SQL generation

### 2. Sample Questions (3-5)

These appear in the Genie UI as conversation starters. Users click them to begin exploring.

**Best practices:**
- Cover different difficulty levels (simple count → join → ratio)
- Use natural language the target audience would actually use
- Include at least one question requiring a join
- Include at least one question with a date filter

**Example set:**
1. "What is the average OEE by plant for 2024?" (aggregation + join)
2. "Which production lines have the highest defect rates?" (ratio + ranking)
3. "Show me downtime trends by month for Michigan plants" (date + state filter)
4. "How many critical safety incidents happened this year?" (simple filter)
5. "Which shift has the best quality performance?" (cross-table join)

### 3. Curated Q→SQL Examples (8-12)

These are question + SQL pairs that teach Genie the correct query patterns. They are the single highest-impact component after instructions.

**Best practices:**
- Focus on queries Genie gets WRONG without help — typically joins, ratios, and subqueries
- Each example should demonstrate a different pattern
- Include the exact table names and column names
- Use CAST and ROUND for clean output (e.g., `CAST(ROUND(AVG(oee_score) * 100, 2) AS DOUBLE)`)
- Sort by ID when pushing to the API (`instructions.example_question_sqls` must be sorted)

**Pattern coverage checklist:**
- [ ] Simple aggregation (COUNT, SUM, AVG)
- [ ] JOIN between two tables
- [ ] JOIN across three tables
- [ ] Date range filter
- [ ] State/location filter (requires plant join)
- [ ] Ratio calculation (defect rate, scrap rate)
- [ ] Subquery with HAVING
- [ ] MIN/MAX with GROUP BY

### 4. Benchmarks / Evaluation Questions (8-12)

These are questions with known ground truth answers used to score Genie's accuracy automatically.

**Two different APIs — do NOT confuse them:**

| What | API | Where it appears in UI |
|------|-----|----------------------|
| **Benchmarks** (scoring questions) | `POST /api/2.0/data-rooms/{id}/curated-questions` with `question_type: BENCHMARK` | **Benchmark tab** |
| **Curated SQL examples** (teaching pairs) | `PATCH /api/2.0/genie/spaces/{id}` with `serialized_space.instructions.example_question_sqls` | **SQL Queries & functions panel** |

Using the wrong API puts content in the wrong panel. Benchmarks pushed via `serialized_space` appear as SQL examples (wrong). SQL examples pushed via `data-rooms` appear as benchmarks (wrong).

**Benchmark API pattern:**
```python
# Push benchmarks
requests.post(f"{host}/api/2.0/data-rooms/{space_id}/curated-questions",
    headers=headers,
    json={"curated_question": {"data_space_id": space_id,
          "question_text": question, "question_type": "BENCHMARK",
          "answer_text": ground_truth_sql, "is_deprecated": False},
          "data_space_id": space_id})

# List benchmarks
requests.get(f"{host}/api/2.0/data-rooms/{space_id}/curated-questions",
    headers=headers, params={"question_type": "BENCHMARK"})

# Delete a benchmark
requests.delete(f"{host}/api/2.0/data-rooms/{space_id}/curated-questions/{qid}",
    headers=headers)
```

**Benchmark design principles:**
- Each benchmark should return a **single scalar value** (one number) — easy to score programmatically
- Compute ground truth by running the SQL directly against the same tables
- Use 5% relative tolerance for PASS (rounding differences are expected)
- **NEVER include your evaluation (north-star) questions as benchmarks** — benchmarks teach patterns, evals test generalization
- Teach patterns with different filters/states/time ranges than your eval questions
- Always run benchmarks **programmatically** after pushing — don't just push and hope
- Target 100% on synthetic data (controlled), 85%+ on real-world data
- Re-run benchmarks after every change to instructions or examples

**Scoring framework:**
```
PASS: |genie_answer - ground_truth| / ground_truth <= 0.05
WARN: 0.05 < ratio <= 0.15
FAIL: ratio > 0.15 or Genie couldn't answer
```

**Tracking:**
- Write results to a `genie_benchmark_runs` table with: question, ground_truth, genie_answer, status, timestamp, space_id
- Calculate pass_rate = PASS count / total count
- Alert if pass_rate drops below 70%

### 5. Table and Column Metadata

- Every table should have a `COMMENT` set via `ALTER TABLE ... SET TBLPROPERTIES ('comment' = '...')`
- Comments should describe the grain (one row per what?) and key relationships
- Ambiguous columns need explicit descriptions (is this 0-1 or 0-100?)
- Genie reads table comments to understand context

### 6. A/B Testing Pattern

Create two variants of the same space to quantify the impact of curation:

- **Variant A (configured):** Full instructions + sample questions + curated Q→SQL examples
- **Variant B (blank or no-examples):** Same tables, minimal or no instructions, no examples

Run the same benchmark suite against both. The configured space typically scores 10-30% higher, proving the value of investing in curation.

### Monitoring and Continuous Improvement

**4 monitoring sources:**
1. **Genie UI Monitoring tab** — all Q&A, thumbs up/down, review requests
2. **system.access.audit** — user actions and feedback events
3. **system.query.history** — query execution time and row counts
4. **genie_benchmark_runs table** — benchmark pass rate history

**Improvement loop:**
1. Triage thumbs-down and review requests
2. Fix in priority order: data/views → table comments → join instructions → curated examples → free-text instructions
3. Re-run benchmarks after each change
4. Promote good user interactions as new curated examples
5. Schedule weekly automated benchmark runs — alert on drops

### CI/CD Pattern for Genie Spaces

**3-phase deployment:**
1. **Export:** `GET /api/2.0/genie/spaces/{id}?include_serialized_space=true`
2. **Transform:** Remap `source_catalog.source_schema.table` → `target_catalog.target_schema.table` in the serialized_space JSON
3. **Deploy:** `POST /api/2.0/genie/spaces` (create new) or `PATCH /api/2.0/genie/spaces/{id}` (update existing)

**Round-trip PATCH (safe updates):**
1. Rebuild `serialized_space` from your template/source-of-truth file
2. Apply targeted changes (e.g., remap catalog/schema, add curated examples)
3. PATCH with the new `serialized_space` — the API replaces the entire config
4. Sort `example_question_sqls` by ID before PATCH (API requires sorted order)

---

## Part 3 — Genie REST API Reference (for notebook authors)

> **Note for Genie Code:** This section is reference material for humans writing notebooks that call the API directly (e.g., notebooks 03-05 in this workshop). When a user asks you to **create or configure a Genie space**, use your built-in space creation capability — do NOT generate raw API code from this section. Simply create the space with the tables, instructions, sample questions, and curated examples the user describes.

### Two API Families

Genie has two separate API families that target different parts of the UI:

**1. `genie/spaces` API** — for space config, curated SQL examples, sample questions:
- `POST /api/2.0/genie/spaces` — create a space (with `serialized_space` for full config)
- `PATCH /api/2.0/genie/spaces/{id}` — update config via `serialized_space`
- `POST /api/2.0/genie/spaces/{id}/start-conversation` — ask Genie a question
- `GET /api/2.0/genie/spaces/{id}/conversations/{cid}/messages/{mid}` — poll for answer
- `GET .../query-result/{aid}` — get the numeric result

**2. `data-rooms` API** — for benchmarks and text instructions:
- `POST /api/2.0/data-rooms/{id}/curated-questions` — add benchmark (`question_type: BENCHMARK`)
- `GET /api/2.0/data-rooms/{id}/curated-questions?question_type=BENCHMARK` — list benchmarks
- `DELETE /api/2.0/data-rooms/{id}/curated-questions/{qid}` — remove a benchmark
- `POST /api/2.0/data-rooms/{id}/instructions` — add text instruction
- `GET /api/2.0/data-rooms/{id}/instructions` — list instructions

**Common mistake:** Pushing benchmarks via `serialized_space.instructions.example_question_sqls` — this puts them in the SQL Queries panel, NOT the Benchmark tab. Always use `data-rooms/curated-questions` for benchmarks.

### Authentication on Serverless

**Always use:**
```python
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()
host = w.config.host.rstrip("/")
headers = {**w.config.authenticate(), "Content-Type": "application/json"}
```

**Never use:**
- `w.config.token` — returns `None` on serverless compute (Spark Connect). The 401 error message ("Credential was not sent or was of an unsupported type") gives no hint that this is the cause.
- `dbutils.notebook.entry_point...apiToken()` — deprecated and unreliable across compute types.

`w.config.authenticate()` returns the correct auth headers for all compute types (classic clusters, serverless, Spark Connect, jobs).

### `serialized_space` JSON Schema (Version 2)

The `serialized_space` field is a **JSON string** (not a nested object) passed in the POST or PATCH body. This is the only way to set instructions, curated examples, and sample questions.

```json
{
  "version": 2,
  "config": {
    "sample_questions": [
      {"id": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4", "question": ["What is the average OEE by plant?"]}
    ]
  },
  "data_sources": {
    "tables": [
      {"identifier": "catalog.schema.table_name"}
    ]
  },
  "instructions": {
    "text_instructions": [
      {"id": "b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5", "content": ["Line 1 of instructions", "Line 2..."]}
    ],
    "example_question_sqls": [
      {
        "id": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",
        "question": ["What is the defect rate by line?"],
        "sql": ["SELECT line_id, COUNT(CASE WHEN event_type = 'defect_detected' THEN 1 END) ..."]
      }
    ]
  },
  "benchmarks": {
    "questions": [
      {
        "id": "c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6",
        "question": ["How many defects in 2024?"],
        "answer": [{"format": "SQL", "content": ["SELECT COUNT(*) FROM ..."]}]
      }
    ]
  }
}
```

**Critical rules:**
- All `id` values must be **32-character lowercase hex** strings: `uuid.uuid4().hex`
- `example_question_sqls` must be **sorted by `id`** — unsorted arrays cause `INVALID_PARAMETER_VALUE`
- `question` and `sql` are **arrays of strings**, not plain strings
- `content` in `text_instructions` is an **array of strings** (each line/paragraph is a separate element)
- `text_instructions` items also have an `id` field — preserve the existing one when updating
- `benchmarks.questions` entries have `id`, `question` (array), and `answer` (array of `{"format": "SQL", "content": ["sql"]}`)
- `version: 2` must always be set explicitly
- Flat fields like `sql_instructions` or `curated_questions` at the top level of the POST body are **not recognized** — everything goes inside `serialized_space`

### Reading `serialized_space` (GET with `include_serialized_space`)

By default, `GET /api/2.0/genie/spaces/{id}` returns only space metadata (title, description, warehouse_id). To read the full configuration, add the query parameter `include_serialized_space=true`:

```python
space = requests.get(
    f"{host}/api/2.0/genie/spaces/{space_id}",
    headers=headers,
    params={"include_serialized_space": "true"},
).json()
config = json.loads(space["serialized_space"])
```

This returns the complete blob: `version`, `instructions` (text_instructions, example_question_sqls), `data_sources`, `config` (sample_questions), and `benchmarks` (questions).

### Updating `serialized_space` (GET-merge-PATCH)

`PATCH /api/2.0/genie/spaces/{id}` with `serialized_space` does a **full replace** of the blob. To update only one section (e.g., instructions) without wiping everything else, always use the read-modify-write pattern:

1. **GET** with `include_serialized_space=true`
2. **Modify** the specific section in the parsed JSON
3. Set `config["version"] = 2` explicitly
4. **PATCH** with `json.dumps(config)`

Important rules for the modify step:
- `text_instructions` is limited to **1 item** (the Genie Workbench truncates to the first)
- Each `text_instructions` item has `id` (32-char hex) and `content` (list of strings) — preserve the existing `id`
- Keep your template JSON file as the single source of truth for initial space creation

### Dedup / Idempotency

Before creating a space, always check if one with the same title already exists:

```python
def list_spaces():
    r = requests.get(f"{host}/api/2.0/genie/spaces", headers=headers)
    r.raise_for_status()
    return r.json().get("spaces", [])

for s in list_spaces():
    if s.get("title") == my_title:
        # PATCH instead of POST
        requests.patch(f"{host}/api/2.0/genie/spaces/{s['space_id']}", ...)
        break
else:
    # POST new space
    requests.post(f"{host}/api/2.0/genie/spaces", ...)
```

Without this guard, every notebook re-run creates a duplicate space.

### UI URL Construction

The Genie web UI uses `/genie/rooms/` (not `/genie/spaces/`). Azure workspaces need `?o=<workspace_id>`:

```python
import re
def genie_ui_room_url(space_id):
    m = re.search(r"adb-(\d+)\.", host)
    o_param = f"?o={m.group(1)}" if m else ""
    return f"{host}/genie/rooms/{space_id}{o_param}"
```

### Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| 401 "Credential was not sent" | Using `w.config.token` (None on serverless) | Use `w.config.authenticate()` |
| 400 `INVALID_PARAMETER_VALUE` | `example_question_sqls` not sorted by `id` | Add `.sort(key=lambda x: x["id"])` before PATCH |
| 400 "unknown field" | Flat fields like `sql_instructions` in POST body | Move everything into `serialized_space` JSON string |
| 409 Conflict | Space with same title already exists | List spaces first, PATCH if found |
| 404 on GET `serialized_space` | Field is write-only, not returned by GET | Rebuild from template, don't try to read it |
