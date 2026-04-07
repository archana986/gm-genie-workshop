# Manufacturing Genie workshop — Implementation Plan

**Prerequisite reading:** [REQUIREMENTS.md](./REQUIREMENTS.md)  
**Pedagogy:** Standard Genie workshop arc adapted for manufacturing.  
**Manufacturing data reference:** [Manufacturing_Workshop](../../Manufacturing_Workshop) (root-level folder in this workspace)

---

## 1. Goals (summary)

1. **Story arc:** data → Genie → trust (benchmarks) → exploration → Genie Code → governance → app.  
2. **Manufacturing domain:** OEE, FPY, defect/scrap/downtime, safety, equipment feedback — synthetic but realistic.  
3. **Differentiators:** **blank vs configured** Genie comparison; **expanded monitoring**; **deeper Genie Code**; benchmarks tied to **shop-floor metrics**.

---

## 2. Phased delivery

### Phase A — Foundation (Week 1)

| Step | Deliverable | Notes |
|------|-------------|--------|
| A1 | `01_setup_data.ipynb` | Port generation logic from Manufacturing_Workshop `setup.ipynb`; unify naming to `CATALOG` / `SCHEMA` variables; add table/column comments for Genie. |
| A2 | `manufacturing_genie_configured.json` | Adapt `manufacturing_genie_space.json` to use `${CATALOG}.${SCHEMA}` placeholders in docs; ship as template + notebook string replace. |
| A3 | `02_create_genie_spaces.ipynb` | Create **two** spaces (blank + configured); write `workshop_config` keys; SDK + UI fallback. |
| A4 | `README.md` | Prerequisites, run order, parameter table, link to REQUIREMENTS. |

### Phase B — Trust & comparison (Week 2)

| Step | Deliverable | Notes |
|------|-------------|--------|
| B1 | `03_genie_benchmarks.ipynb` | Benchmark notebook; manufacturing FR-EVAL set; ground truth from Spark. |
| B2 | `04_talk_with_data.ipynb` | Guided questions; facilitator cells for **same prompt** against blank vs configured IDs. |
| B3 | `TEST_LOG.md` | Start recording environment, DBR, pass/fail per run. |

### Phase C — Genie Code, monitoring, app (Week 2–3)

| Step | Deliverable | Notes |
|------|-------------|--------|
| C1 | `05_genie_code_skills.ipynb` | Hands-on checklist; manufacturing examples only. |
| C2 | `skill/manufacturing-genie-context/SKILL.md` + `skill/genie-space-builder/SKILL.md` | Per FR-GC-03: no hardcoded customer catalog in committed text — use placeholders. |
| C3 | `08_monitoring_observability.ipynb` | Query patterns + “if not available” notes; optional export Lakeview JSON for benchmark trends. |
| C4 | `06_security_governance.ipynb` | Plant/line RLS or masked columns on manufacturing / PII-like fields. |
| C5 | `08_deployment` + `app/*` | Databricks App sample; env-based space id (see notebook 08 Option B). |

### Phase D — Hardening & publish (before Apr 15)

| Step | Deliverable | Notes |
|------|-------------|--------|
| D1 | Three+ full dry runs | Update TEST_LOG; fix flakes (warehouse cold start, API timeouts). |
| D2 | Contingency doc in README | Warehouse backup, manual Genie creation, API restrictions. |
| D3 | Git init + push | NFR-REL-01; `.gitignore` for local `.env`; no tokens. |

---

## 3. Dependency chain (target)

```
01_setup_data
    └── creates Delta tables + functions + comments

02_create_genie_spaces
    └── creates Genie Space (blank) + Genie Space (configured)
    └── workshop_config: genie_space_id_blank, genie_space_id_configured (+ URLs)

03_genie_benchmarks
    └── reads configured space id (default); optional blank id for contrast
    └── writes genie_benchmark_runs (or equivalent)

04_talk_with_data
    └── reads workshop_config; NL exploration + A/B prompts

05_genie_code_skills
    └── skills under skill/; workspace import paths documented

06_compare_genie_spaces
    └── A/B benchmarks; genie_benchmark_runs

07_security_governance
    └── views / masks on manufacturing tables

08_deployment_best_practices
    └── Playground, App bundle, Jobs, CI/CD export

09_monitoring_observability
    └── reads benchmark history + system tables (best effort)
```

**Rule:** No notebook should require copying Genie Space IDs by hand once 02 completes successfully.

---

## 4. Live agenda mapping (example half-day)

| Block | Notebook(s) | Notes |
|-------|-------------|--------|
| Load data | 01_setup_data | Emphasize **metric definitions** in comments |
| Build Genie | 02 | **Two spaces**; wow moment on configured space first |
| Talk with data | 04 | Add **5 min** blank vs configured |
| Evals | 03 | Manufacturing KPI benchmarks |
| App / deploy | 08 (Options A–B) | Shorten if time-constrained |
| Genie Code | 05 | **15–25 min** hands-on |
| Security | 07 | Masking / Data Room |
| Monitoring | 09 | Production readiness / observability |
| CI/CD | 08 Option D | Optional deep dive |
| Q&A | — | Buffer |

**Time risk:** Adding 08 may require shortening app or governance; see REQUIREMENTS open decision on duration.

---

## 5. File layout (target repo)

```
manufacturing-genie-workshop/
├── README.md
├── SETUP.md
├── CODE_WORKINGS.md
├── REQUIREMENTS.md
├── PLAN.md
├── TEST_LOG.md                 # created during QA
├── notebooks/
│   ├── 01_setup_data.ipynb
│   ├── 02_create_genie_spaces.ipynb
│   ├── 03_genie_evals_benchmarks.ipynb
│   ├── 04_talk_with_data.ipynb
│   ├── 05_genie_code_skills.ipynb
│   ├── 06_compare_genie_spaces.ipynb
│   ├── 07_security_governance.ipynb
│   ├── 08_deployment_best_practices.ipynb
│   └── 09_monitoring_observability.ipynb
├── templates/
│   └── manufacturing_genie_configured.json   # or single JSON with blank body variant
├── skill/
│   ├── manufacturing-genie-context/SKILL.md
│   └── genie-space-builder/SKILL.md
└── app/
    ├── app.py
    ├── app.yaml
    └── requirements.txt
```

---

## 6. Risk register (preview)

| Risk | Mitigation |
|------|------------|
| Genie API cannot create second space quickly | Pre-create spaces; 02 only validates IDs; document UI path |
| System tables unavailable for monitoring | 08 uses benchmark Delta + documented manual checks |
| Benchmark flakiness (LLM variance) | Prefer numeric extractions + tolerances; fixed seed data |
| Workshop overtime | Cut 07 or shrink 06; never cut 03/04 core story |

---

## 7. Next step (after plan approval)

Implement Phase A in order: **01** → **configured JSON template** → **02** (dual space) → **README**. Then iterate benchmarks and monitoring.

When you confirm **catalog/schema naming**, **GitHub remote**, and **monitoring availability** in the target workspace, execution can proceed without rework on identifiers or SQL.
