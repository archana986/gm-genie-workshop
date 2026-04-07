# Workshop Prompt — Build a Genie Space with Genie Code

Copy the prompt below into **Genie Code** (with both skills installed) to have it create a Genie space from your Unity Catalog tables.

---

## Prerequisites

Before running this prompt:

1. Run **notebook 01** (`01_setup_data`) to create the manufacturing tables.
2. Have your **SQL warehouse ID** ready (from the warehouse URL or `databricks warehouses list`).
3. Install both skills in `.assistant/skills/`:
   - `manufacturing-genie-context/SKILL.md`
   - `genie-space-builder/SKILL.md`

---

## The Prompt

```
I need you to create a Databricks Genie SQL space for manufacturing analytics using the REST API.

Here are my details:
- Catalog: workshop_demo
- Schema: genie_workshop_manufacturing
- Warehouse ID: <paste your warehouse ID here>

The schema has these 7 tables: plants, production_lines, operators, production_events, quality_metrics_daily, safety_incidents, equipment_feedback.

Using the genie-space-builder skill, please:

1. First, run DESCRIBE TABLE on each of the 7 tables to understand the columns and types.

2. Then create a well-configured Genie space via POST /api/2.0/genie/spaces with:

   a) A descriptive title and description for manufacturing quality analytics.

   b) All 7 tables attached (sorted by fully qualified identifier).

   c) Comprehensive text instructions covering:
      - Business context (automotive manufacturing with multiple plants and shifts)
      - Metric definitions with exact formulas (OEE, FPY, defect rate, scrap rate, downtime)
      - Threshold classifications (high performing, at risk, maintenance priority)
      - Every join relationship between tables
      - Column naming gotchas (e.g., "date" not "metric_date", production_line_id not line_id)
      - Event type mappings from production_events
      - Defect code prefixes and their meanings
      - Shift definitions

   d) 10 curated example Q-to-SQL pairs covering:
      - Total production events
      - Lines with defect rates above threshold
      - Average OEE by plant
      - FPY trend by month
      - Top operators by defects detected
      - Top defect codes
      - Downtime comparison across plants
      - Quality by shift
      - Critical safety incidents
      - Scrap rate by product type

   e) 3-5 sample questions for the UI.

3. After creating the space, print the browser URL (using /genie/rooms/ not /genie/spaces/).

4. Then open the space and test it by asking: "What is the average OEE by plant?"

Make sure to follow the serialized_space v2 structure exactly — tables sorted, all IDs unique via uuid4, text instructions as content array, curated SQL with fully qualified table names.
```

---

## Variations

### Minimal prompt (for experienced users)

```
Create a Genie space on catalog `workshop_demo`, schema `genie_workshop_manufacturing`, warehouse `<ID>`. Attach all 7 tables. Use the genie-space-builder skill for the API pattern. Write thorough instructions covering OEE, FPY, defect rate formulas, all join paths, and column naming. Add 10 curated Q-to-SQL examples. Print the browser URL when done.
```

### Bring-your-own-data prompt (generic)

```
I want to create a Databricks Genie SQL space for my data.

- Catalog: <your_catalog>
- Schema: <your_schema>
- Warehouse ID: <your_warehouse_id>

Using the genie-space-builder skill:

1. List and DESCRIBE all tables in my schema.
2. Identify the key metrics, join relationships, and column naming conventions.
3. Draft comprehensive text instructions for Genie.
4. Write 8-10 curated Q-to-SQL examples covering the most common analytical questions for this data.
5. Create the Genie space via the REST API.
6. Print the browser URL.
7. Test with a representative question.
```

---

## What to expect

Genie Code will:
1. Inspect your tables to understand the schema.
2. Generate a `serialized_space` payload following the v2 structure.
3. POST to `/api/2.0/genie/spaces` to create the space.
4. Return a clickable URL to open the space in the Genie UI.

The whole process takes about 2-3 minutes. After creation, open the space in the browser and test 3-5 questions to validate quality. Use the **validation loop** from the skill to iterate.
