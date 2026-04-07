---
name: gm-genie-manufacturing-context
description: Manufacturing quality (OEE, FPY, defects) and joins for Genie Code on GM Genie workshop tables.
---

# GM manufacturing Genie context

## Catalog and schema

Replace `CATALOG.SCHEMA` with your workshop location (defaults: `gm_ama_demos.genie_workshop_manufacturing`).

## Genie spaces in this workshop

Nine-step flow: **02** creates three SQL Genie spaces (blank, **with** curated examples, **without**). **03** defines evals and pushes BENCHMARK rows to the primary space. **05** + skills for Genie Code. **06** A/B-benchmarks with vs without in-space examples. **07** masks **`unit_serial_vin`** via `production_events_restricted` + Genie proof. **08** deployment, **09** monitoring.

## Metrics

- **OEE:** `quality_metrics_daily.oee_score` is 0–1; multiply by 100 for percent. Target bands often 85%+ good, 75%+ acceptable.
- **First pass yield:** `quality_metrics_daily.first_pass_yield` same 0–1 scale.
- **Defect rate:** `COUNT` where `event_type = 'defect_detected'` divided by `COUNT` where `event_type = 'unit_produced'` on `production_events`, typically filtered by line and date.
- **Downtime:** `quality_metrics_daily.downtime_minutes` per line per day.

## Joins

- `production_events.production_line_id` → `production_lines.line_id`
- `production_lines.plant_id` → `plants.plant_id`
- `quality_metrics_daily.production_line_id` → `production_lines.line_id`
- `safety_incidents.production_line_id` → `production_lines.line_id`

## Column naming

- Daily quality date column: `quality_metrics_daily.date` (not `metric_date`).
- `production_events.unit_serial_vin`: 17-character unit traceability id (VIN-style). For broad audiences use view `production_events_restricted` (workshop **07** masks it for non-`admin_group`).
- Use fully qualified names: `CATALOG.SCHEMA.table_name`.
