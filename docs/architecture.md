# Architecture

## 1. The problem

*Meridian Health Network* is a group of hospitals. Patient, doctor and hospital records live in an
internal operational database. Every day the network also receives **lab results** and **insurance
provider** files from external partners as CSVs. Today, combining these is manual and error-prone:

- Data lives in different places with no automatic way to line it up.
- New data arriving in source systems is not picked up automatically.
- Downstream reports silently go stale, and nobody notices until a number is wrong.

## 2. The solution approach

Build a **metadata-driven** ingestion framework in Azure Data Factory that reads a control table and
loads any configured source into the lake, then process it through a **medallion architecture** on
Databricks with full auditing and email alerting on failure.

The design goal: **onboarding a new table is a config change, not an engineering change.**

## 3. Sources

| Source system | Object | Load type |
|---|---|---|
| PostgreSQL (Neon) | `public.hospitals` | full |
| PostgreSQL (Neon) | `public.doctors` | full |
| PostgreSQL (Neon) | `public.patients` | merge (incremental upsert) |
| ADLS CSV (partner) | `lab_results` | append (incremental) |
| ADLS CSV (partner) | `insurance_providers` | full |

## 4. Layers (medallion)

| Layer | Content | Format | Notes |
|---|---|---|---|
| **Landing** | Raw copy exactly as pulled from source | Parquet / CSV | Partitioned `source/table/<yyyyMMdd_HHmmss>/` |
| **Bronze** | Landing data + ingestion audit columns | Delta | `_ingested_at`, `_source_file`, `_run_id` |
| **Silver** | Cleaned, typed, deduplicated, conformed | Delta | Business rules, null handling, keys enforced |
| **Gold** | Business-ready marts / KPIs | Delta | Joins across silver; aggregated for consumption |

## 5. Load types

- **full** — truncate-and-load; the target is replaced every run. Used for small dimension-like
  tables (hospitals, doctors, insurance providers).
- **append** — only new rows since the last watermark are read and appended. Used for immutable
  event-style feeds (lab results).
- **merge** — read rows changed since the last watermark, then upsert into the target using
  `merge_keys` (insert new, update changed). Used for slowly-changing entities (patients).

Incremental logic is driven by `watermark_column` and the `control.watermark` table, which stores the
last successfully processed value per table.

## 6. Landing folder structure

Written dynamically by ADF so runs never collide:

```
landing/
└── <source_system>/            e.g. postgres
    └── <table_name>/           e.g. patients
        └── <yyyyMMdd_HHmmss>/   e.g. 20260928_113045
            └── part-*.parquet
```

The timestamp folder means every run is reproducible and you always know which file a load read.

## 7. Metadata & audit (Azure SQL — `control` schema)

- **`table_config`** — the driving table; one row per ingested object (see README for columns).
- **`watermark`** — last processed watermark value per table id, for incremental loads.
- **`audit_log`** — one row per stage execution: `run_id`, `table_id`, `stage`, `status`
  (in_progress / success / failed), `records_written`, `start_time`, `end_time`. Powers monitoring
  and the failure-alert email.

## 8. Orchestration (ADF)

Two pipelines keep the loop clean:

- **`pl_source_to_silver_main`** — looks up active tables for a given `source_system`, then a
  `ForEach` calls the inner pipeline once per `table_id`.
- **`pl_source_to_silver_inner`** — for one `table_id`: read its config, set a run timestamp, copy
  source → landing on a dynamic path, and (optionally) trigger the Databricks job for
  landing→bronze→silver.

See [`../adf/README.md`](../adf/README.md).

## 9. Governance & security

- **Unity Catalog** governs Databricks access via storage credential → external location → volume
  (see [`../databricks/setup/adls_connection.md`](../databricks/setup/adls_connection.md)).
- **Key Vault** holds source passwords; ADF reads them through a linked service (never hard-coded).
- Databricks uses a Unity Catalog **access connector** (managed identity) rather than account keys.

## 10. CI/CD

Both ADF and the Databricks workspace are integrated with GitHub. Pipeline JSON and notebooks are
version-controlled; changes flow through branches and a publish branch, giving a reviewable history
and a path to promote across environments.

## 11. Consumption

- A **Databricks SQL dashboard** over the gold layer for KPIs.
- **Genie** for natural-language questions against the gold tables, aimed at business users.
