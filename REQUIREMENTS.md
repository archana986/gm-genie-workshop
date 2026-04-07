# Manufacturing Genie workshop — Requirements

**Status:** Draft (planning)  
**Target hardening:** Battle-test notebooks multiple times before **April 15, 2026**  
**Distribution:** Shared GitHub repository (URL TBD; see Open decisions)

---

## 1. Purpose

Deliver a **Databricks Genie + Apps** workshop for **manufacturing / shop-floor analytics** audiences, following a **standard Genie enablement arc** (setup → Genie Space → benchmarks → exploration → Genie Code → governance → app) with **manufacturing-shaped synthetic data and metrics** aligned with [Manufacturing_Workshop](../../Manufacturing_Workshop) (plants, lines, events, OEE, quality, safety).

Primary outcomes for participants:

- See **measurable value of Genie context** (instructions, curated SQL, table descriptions) via a **blank vs. configured Genie Space** comparison.
- Run **benchmarks / evaluation** grounded in **real manufacturing KPIs** (OEE, first pass yield, defect rate, downtime, scrap, safety severity), not generic “total spend” style questions.
- Understand **operational monitoring** patterns for Genie (usage, quality of answers, benchmark trends) suitable for pilot → production conversations.
- Complete an optional path for **Genie Code + Skills** with manufacturing-relevant `SKILL.md` examples.
- Optionally deploy a **Databricks App** that talks to the same Genie Space (Gradio sample under `app/`).

---

## 2. Stakeholder ideas (traceability)

| Source | Idea | Requirement ID |
|--------|------|------------------|
| Eric | Side-by-side **blank vs. configured** Genie Space demo to show value of context | FR-CTX-01 … FR-CTX-03 |
| Archana | Convert template to **manufacturing data + metrics** (OEE, etc.) | FR-DATA-01 … FR-DATA-04 |
| Archana | Add **monitoring** section | FR-MON-01 … FR-MON-04 |
| Archana | Add **Genie Code** section (expand beyond 5-minute awareness) | FR-GC-01 … FR-GC-03 |
| Archana | **Benchmark / evaluation** with manufacturing metrics | FR-EVAL-01 … FR-EVAL-05 |
| Archana | **Push to shared GitHub repo** | NFR-REL-01 |
| Archana | **Battle-test** notebooks repeatedly before Apr 15 | NFR-QA-01 |

---

## 3. Scope

### 3.1 In scope

- Notebooks and assets under this repo following the **module order** in PLAN.md.
- **Unity Catalog** catalog/schema (configurable via Python variables; no `spark.conf.set` for app config per workspace rules).
- **Synthetic manufacturing dataset** structurally aligned with Manufacturing_Workshop: plants, production_lines, operators, production_events, quality_metrics_daily, safety_incidents, equipment_feedback; SQL helpers where useful (`compute_oee_summary`, defect rate, etc.).
- **Genie Space** creation via notebook (SDK) with fallback to UI + `workshop_config` persistence.
- **Benchmark notebook** that: defines questions + numeric/text ground truth from Spark; calls Genie Conversation API; records PASS/FAIL; persists run history to Delta.
- **Monitoring notebook** (or dedicated section): what to track (Genie usage, benchmark pass rate, latency buckets, instruction drift), using **system tables / Lakeview / SQL** where the workspace supports it; document fallbacks if APIs differ.
- **Genie Code + Skills**: manufacturing-themed skills under `skill/`; notebook walkthrough with copy-paste-safe steps.
- **Security / governance** module: row filters, column masks, or restricted views on plant/line (mirror Manufacturing_Workshop “filtering and masking” intent, adapted to multi-notebook flow).
- **README** with prerequisites, parameter table, and “run order”.
- **Git**: initialize repo in `manufacturing-genie-workshop/`, push to org-approved shared GitHub (see Open decisions).

### 3.2 Out of scope (initial cut)

- Connecting to customer **live** MES/SCADA (workshop uses **synthetic** data only unless explicitly added later).
- Custom ML models beyond Genie / warehouse SQL.
- Non-Databricks front-ends except the reference Databricks App.

### 3.3 Assumptions

- Workshop runs on **Databricks** with Genie, SQL warehouse, and UC enabled.
- Facilitators have permission to create catalog/schema (or use pre-provisioned catalog).
- Participants use **serverless** or classic compute consistent with notebook compatibility rules in this workspace.

---

## 4. Functional requirements

### 4.1 Data & domain (manufacturing)

| ID | Requirement |
|----|-------------|
| FR-DATA-01 | `01_setup_data` creates all core tables and documents **column meanings** for Genie (table/column comments or companion markdown in notebook). |
| FR-DATA-02 | Metrics definitions are **explicit** in Genie instructions: OEE (0–1 vs %), first pass yield, defect rate formula from `production_events`, downtime minutes, scrap rate, safety severity bands. |
| FR-DATA-03 | Seed data yields **stable ground-truth answers** for benchmarks (deterministic or seeded random). |
| FR-DATA-04 | Optional: reuse or adapt SQL/function patterns from Manufacturing_Workshop `setup.ipynb` / `manufacturing_genie_space.json` (curated questions, join keys, naming pitfalls). |

### 4.2 Genie Space & context comparison (Eric’s demo)

| ID | Requirement |
|----|-------------|
| FR-CTX-01 | Provide a **“blank”** Genie Space variant: same tables attached, **minimal** instructions (or generic only). |
| FR-CTX-02 | Provide a **“configured”** space: full manufacturing instructions + sample SQL + curated questions (equivalent depth to `manufacturing_genie_space.json`). |
| FR-CTX-03 | Facilitator script / notebook cells: run **2–3 identical natural-language questions** against both spaces; capture qualitative + simple quantitative contrast (e.g., wrong join, wrong metric definition, timeout). |
| FR-CTX-04 | Persist both `space_id`s (or document manual path) in `workshop_config` with keys e.g. `genie_space_id_configured`, `genie_space_id_blank`. |

### 4.3 Benchmarks & evaluation (manufacturing metrics)

| ID | Requirement |
|----|-------------|
| FR-EVAL-01 | Minimum **8 benchmark questions** spanning: OEE by plant, FPY trend, defect rate threshold, downtime comparison, scrap by product type, shift quality, safety critical list, top defect codes (adjustable list). |
| FR-EVAL-02 | Each benchmark has **machine-checkable** expected outcome (numeric tolerance or row count / ordered key set). |
| FR-EVAL-03 | Results stored in Delta (e.g. `genie_benchmark_runs`) with timestamp, question id, pass/fail, extracted value, error message. |
| FR-EVAL-04 | Notebook teaches **debug loop**: failure → inspect Genie SQL → update instructions or ground truth → re-run. |
| FR-EVAL-05 | **Configured space** is the default target for benchmarks; optional stretch: run subset against **blank** space to show lower pass rate. |

### 4.4 Monitoring

| ID | Requirement |
|----|-------------|
| FR-MON-01 | Document **what to monitor** for a Genie pilot: adoption (questions/day), benchmark pass rate, p95 time-to-answer, top failure themes. |
| FR-MON-02 | Provide **executable examples** where possible: SQL against `system.*` (e.g. query history, audit) or Genie-related telemetry if available in the target workspace; label **workspace-dependent** queries clearly. |
| FR-MON-03 | Optional Lakeview JSON or notebook-built charts for **benchmark trend over time**. |
| FR-MON-04 | Call out **privacy / compliance** boundaries (no PII in logs; aggregate only). |

### 4.5 Genie Code & Skills

| ID | Requirement |
|----|-------------|
| FR-GC-01 | Dedicated notebook section (or standalone notebook) **≥ 15 minutes** of material: install path, invoking Genie Code, loading a skill. |
| FR-GC-02 | At least **two** skills: e.g. `manufacturing-genie-context` (metric definitions + join graph) and `genie-space-builder` (space API patterns). |
| FR-GC-03 | Skills use **parameterized catalog.schema** in prose (“replace with your catalog.schema”) — no hardcoded customer names in committed files. |

### 4.6 App deployment

| ID | Requirement |
|----|-------------|
| FR-APP-01 | Reference app under `app/` (Gradio or equivalent) reads space id from env or config; README documents deploy steps. |
| FR-APP-02 | Notebook **07_deploy_app** auto-reads configured `genie_space_id` from `workshop_config`. |

### 4.7 Governance

| ID | Requirement |
|----|-------------|
| FR-GOV-01 | Notebook demonstrates **restricted view** or **dynamic row filter** by plant (or similar) and documents analyst vs restricted role. |

---

## 5. Non-functional requirements

| ID | Requirement |
|----|-------------|
| NFR-QA-01 | Full dry run of notebooks **at least 3 times** on target-style workspace before Apr 15; record pass/fail matrix in `TEST_LOG.md` (created during QA). |
| NFR-QA-02 | Notebooks follow workspace rules: **markdown before each code cell**, no `---` in markdown, config via **Python variables** (no `spark.conf.set` for custom app keys). |
| NFR-REL-01 | Repository pushed to **shared GitHub** with LICENSE/access per org policy; no secrets in repo. |
| NFR-USE-01 | Single **dependency chain**: no manual copy-paste of space IDs once `workshop_config` is populated. |
| NFR-DOC-01 | `README.md` lists **notebook order**, estimated timing, and contingency (API failure, manual Genie creation). |

---

## 6. Notebook inventory (target)

Module numbering is stable; additions marked **(new)**.

| # | Notebook | Purpose |
|---|----------|---------|
| 01 | `01_setup_data.ipynb` | Manufacturing tables + comments + verification KPIs |
| 02 | `02_create_genie_spaces.ipynb` | Create **blank + configured** spaces; save IDs to `workshop_config` |
| 03 | `03_genie_benchmarks.ipynb` | Manufacturing benchmark suite + Delta history |
| 04 | `04_talk_with_data.ipynb` | Guided NL questions; optional A/B prompts blank vs configured |
| 05 | `05_genie_code_skills.ipynb` | Expanded Genie Code + Skills |
| 06 | `06_security_governance.ipynb` | UC, masking, restricted views |
| 07 | `07_deploy_app.ipynb` | App upload + deploy |
| — | `08_monitoring_observability.ipynb` **(new)** | Monitoring patterns + optional dashboards |
| — | `00_workshop_prereqs.md` **(optional)** | Checklist only (or first markdown in README) |

Exact split (e.g. monitoring as 08 vs folded into 03/04) is an **open decision**; see PLAN.md.

---

## 7. Open decisions (need owner input before build)

1. **GitHub remote:** Organization, repo name, default branch, and whether repo is **public** or **internal-only**.
2. **Default catalog/schema names:** e.g. `workshop_demo.genie_workshop_manufacturing` vs reuse `main.manufacturing_quality_analytics` for parity with Manufacturing_Workshop clone.
3. **Monitoring implementation:** Which system tables / features are **guaranteed** in the pilot workspace (query history, audit, Genie-specific telemetry)? Plan lists fallbacks.
4. **Blank vs configured:** Two long-lived spaces vs single space + instruction swap (if API supports update without duplicating spaces).
5. **Workshop duration:** Half-day (~3h) vs shorter executive demo; drives depth of modules 05 and 08.
6. **Slides:** Reuse Manufacturing_Workshop deck vs new Google Slides; link from README when available.

---

## 8. Acceptance criteria (MVP)

- [ ] Running 01→02→03 on a clean schema completes without manual ID paste.
- [ ] Benchmarks achieve **≥ 85% pass** on configured space after instruction tuning.
- [ ] Facilitator can run **blank vs configured** comparison in **≤ 10 minutes** live.
- [ ] Monitoring notebook runs **or** clearly documents blocked APIs with alternative manual checks.
- [ ] Genie Code notebook completes with **both** skills discoverable from documented paths.
- [ ] README + REQUIREMENTS + PLAN committed; GitHub push completed per NFR-REL-01.
- [ ] TEST_LOG shows **3+** full dry runs before Apr 15.

---

## 9. References (in-repo)

- Internal planning notes: PLAN.md in this folder.
- Data & metric definitions: `../../Manufacturing_Workshop/README.md`, `../../Manufacturing_Workshop/manufacturing_genie_space.json`
