---
name: genie-space-builder
description: Generic skill for creating and configuring Databricks Genie spaces programmatically via REST API. Covers serialized_space payload structure, API endpoints, best practices for instructions/curated SQL, and the validation loop.
---

# Genie Space Builder — Skill for Genie Code

Use this skill to create, configure, and update Databricks Genie SQL spaces programmatically using the REST API from a Databricks notebook.

---

## 1. Prerequisites

Before creating a Genie space you need:

- **Unity Catalog tables** already created with table and column comments.
- **A SQL warehouse ID** — get it from the warehouse URL or via `databricks warehouses list`.
- **Workspace authentication** — use `WorkspaceClient()` from `databricks-sdk`.

```python
from databricks.sdk import WorkspaceClient
import requests, json, uuid, re

w = WorkspaceClient()
host = w.config.host.rstrip("/")
headers = {**w.config.authenticate(), "Content-Type": "application/json"}
```

---

## 2. REST API endpoints

| Action | Method | Endpoint |
|--------|--------|----------|
| Create | POST | `/api/2.0/genie/spaces` |
| Get (with definition) | GET | `/api/2.0/genie/spaces/{space_id}?include_serialized_space=true` |
| Update | PATCH | `/api/2.0/genie/spaces/{space_id}` |
| List all | GET | `/api/2.0/genie/spaces` |

---

## 3. The `serialized_space` payload

The `serialized_space` field is a **JSON string** (not an object) embedded inside the API request body. It follows this structure:

```json
{
  "version": 2,
  "config": {
    "sample_questions": [
      {"id": "<uuid>", "question": ["What is the average OEE by plant?"]}
    ]
  },
  "data_sources": {
    "tables": [
      {"identifier": "catalog.schema.table_a"},
      {"identifier": "catalog.schema.table_b"}
    ]
  },
  "instructions": {
    "text_instructions": [
      {"content": ["Business context and metric definitions go here..."]}
    ],
    "example_question_sqls": [
      {
        "id": "<uuid>",
        "question": ["Which lines have defect rates above 5%?"],
        "sql": ["SELECT ... FROM catalog.schema.table WHERE ..."]
      }
    ]
  }
}
```

### Validation rules (these cause silent failures if violated)

- **`version`** must be `2`.
- **`data_sources.tables`** must be a non-empty list, **sorted ascending by `identifier`**.
- Every `id` field must be a **unique, non-empty string** — use `uuid.uuid4().hex`.
- `sample_questions` and `example_question_sqls` entries must also be sorted by `id`.
- SQL in `example_question_sqls` must use **fully qualified table names** (`catalog.schema.table`).

---

## 4. Create request body

The full POST body wraps `serialized_space` as a string:

```python
body = {
    "title": "My Genie Space",
    "description": "Natural language analytics for ...",
    "warehouse_id": "<warehouse_id>",
    "serialized_space": json.dumps(serialized_space_dict)
}
resp = requests.post(f"{host}/api/2.0/genie/spaces", headers=headers, json=body)
resp.raise_for_status()
space_id = resp.json().get("space_id") or resp.json().get("id")
```

---

## 5. Building the browser URL

Genie UI uses `/genie/rooms/` (not `/genie/spaces/`):

```python
def genie_ui_url(host, space_id):
    m = re.search(r"adb-(\d+)\.", host)
    o = f"?o={m.group(1)}" if m else ""
    return f"{host}/genie/rooms/{space_id}{o}"
```

---

## 6. Writing effective text instructions

Text instructions are the most impactful part of a Genie space. Follow these guidelines:

### What to include

1. **Business context** — one paragraph describing what the data represents and who uses it.
2. **Metric definitions with formulas** — be explicit about scales (e.g., "OEE is stored as 0–1, multiply by 100 for percentage display").
3. **Thresholds and classifications** — e.g., "High performing: OEE >= 85%. At risk: OEE < 70%."
4. **Join relationships** — list every foreign key relationship explicitly: `table_a.col joins to table_b.col`.
5. **Column naming gotchas** — call out any non-obvious names: "The date column is `date`, not `metric_date`."
6. **Event type mappings** — if a table uses event types or status codes, define them.
7. **What NOT to do** — "Do not invent thresholds not listed above."

### What to avoid

- Implementation details about how the warehouse or pipeline works.
- Redundant information already in table/column comments.
- Overly long instructions (Genie performs better with focused, structured text).

### Template

```
Business Context:
This dataset represents [domain] data from [organization] covering [scope]. Use the tables in [catalog.schema] to answer questions about [key areas].

Key Metrics:
- [Metric Name]: [definition]. Stored in [table.column] as [scale]. Target: [threshold].
- ...

Table Relationships:
- [table_a.col] joins to [table_b.col]
- ...

Column Notes:
- [table] uses '[col_name]' (not '[common_wrong_name]') for [meaning].
- ...

Important Rules:
- Always use fully qualified table names with [catalog.schema] prefix.
- When calculating rates, filter by [relevant column] values.
- ...
```

---

## 7. Curated example SQL (example_question_sqls)

These are the highest-signal teaching tool for Genie. Each entry pairs a natural language question with a gold-standard SQL answer.

### Guidelines

- Start with **5–10** curated examples covering your most common question patterns.
- Cover different query shapes: aggregation, filtering, joins, trends, top-N.
- Use fully qualified table names in every SQL statement.
- Make the SQL correct and efficient — Genie may adapt it for similar questions.
- Include at least one example for each important join path.

### Example

```python
curated = [
    {
        "question": "What is the average OEE by plant?",
        "sql": "SELECT p.plant_name, ROUND(AVG(qm.oee_score) * 100, 2) AS avg_oee "
               "FROM catalog.schema.quality_metrics_daily qm "
               "JOIN catalog.schema.plants p ON qm.plant_id = p.plant_id "
               "GROUP BY p.plant_name ORDER BY avg_oee DESC"
    },
    # ... more examples
]
```

---

## 8. Sample questions (config.sample_questions)

These appear in the Genie UI as suggested starting prompts. They are **display only** — no SQL attached.

- Use **3–5** questions that showcase the space's range.
- Write them as a business user would ask (not as SQL queries).
- Cover different tables and metric types.

---

## 9. Complete creation pattern (copy-paste ready)

```python
import json, uuid, requests, re
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
host = w.config.host.rstrip("/")
headers = {**w.config.authenticate(), "Content-Type": "application/json"}

CATALOG = "my_catalog"
SCHEMA = "my_schema"
fqn = f"{CATALOG}.{SCHEMA}"

# 1. Define tables (MUST be sorted)
tables = sorted([
    f"{fqn}.table_a",
    f"{fqn}.table_b",
    f"{fqn}.table_c",
])
tables_config = [{"identifier": t} for t in tables]

# 2. Write instructions
instructions_text = """
Business Context: ...
Key Metrics: ...
Table Relationships: ...
Column Notes: ...
"""

# 3. Build curated Q-to-SQL pairs
curated_questions = [
    {"question": "...", "sql": "SELECT ..."},
]
curated_qs = sorted([
    {"id": uuid.uuid4().hex, "question": [q["question"]], "sql": [q["sql"]]}
    for q in curated_questions
], key=lambda x: x["id"])

# 4. Build sample questions
sample_qs = sorted([
    {"id": uuid.uuid4().hex, "question": [q]}
    for q in ["Question 1?", "Question 2?", "Question 3?"]
], key=lambda x: x["id"])

# 5. Assemble serialized_space
serialized_space = {
    "version": 2,
    "config": {"sample_questions": sample_qs},
    "data_sources": {"tables": tables_config},
    "instructions": {
        "text_instructions": [{"content": [instructions_text]}],
        "example_question_sqls": curated_qs,
    },
}

# 6. Create the space
WAREHOUSE_ID = "<your-warehouse-id>"
body = {
    "title": "My Analytics Space",
    "description": "Natural language exploration of ...",
    "warehouse_id": WAREHOUSE_ID,
    "serialized_space": json.dumps(serialized_space),
}
resp = requests.post(f"{host}/api/2.0/genie/spaces", headers=headers, json=body)
resp.raise_for_status()
space_id = resp.json().get("space_id") or resp.json().get("id")

# 7. Build browser URL
m = re.search(r"adb-(\d+)\.", host)
o = f"?o={m.group(1)}" if m else ""
print(f"Genie Space URL: {host}/genie/rooms/{space_id}{o}")
```

---

## 10. Round-trip update pattern (for existing spaces)

When modifying an existing space, always round-trip to preserve server-managed fields:

```python
# Fetch existing
r = requests.get(
    f"{host}/api/2.0/genie/spaces/{space_id}?include_serialized_space=true",
    headers=headers
)
existing = r.json()
space_def = json.loads(existing["serialized_space"])

# Modify (e.g., update instructions)
space_def["instructions"]["text_instructions"][0]["content"] = [new_instructions]

# Patch back
requests.patch(
    f"{host}/api/2.0/genie/spaces/{space_id}",
    headers=headers,
    json={"serialized_space": json.dumps(space_def)}
).raise_for_status()
```

**Important:** Preserve existing opaque IDs when round-tripping. Only generate new UUIDs for new entries.

---

## 11. Validation loop (iterate to quality)

After creating a space:

1. Open the Genie UI and ask 3–5 representative questions.
2. Check: Did Genie select the right tables? Use the right joins? Apply the right filters?
3. If wrong: follow the **fix order** — data/views first, then metadata, then joins, then examples, then instructions.
4. Convert good interactions into new curated Q-to-SQL pairs.
5. Re-test after each change.

---

## 12. Anti-patterns to avoid

- Adding raw bronze/staging tables (use gold/semantic layer tables).
- Adding many tables before validating the first 5 questions.
- Leaving title, description, or instructions generic.
- Depending on joins that aren't documented in instructions.
- Writing instructions that describe pipeline architecture instead of business rules.
