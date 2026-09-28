# How to describe this project — CV, LinkedIn, interview

The honest, defensible way to present this. It's a self-built learning project on synthetic data —
say so, and let the *engineering* do the talking. Recruiters value a candidate who built the modern
stack end to end far more than they penalise "personal project."

---

## CV — project block (drop into the Projects section)

**Metadata-Driven Healthcare Lakehouse — Azure Data Factory & Databricks** *(personal project, 2026)*

- Built an end-to-end, **config-driven ingestion framework** in Azure Data Factory that loads any
  source defined in a control table (PostgreSQL + CSV) into ADLS Gen2 — onboarding a new table is a
  metadata row, not a new pipeline.
- Implemented a **Bronze → Silver → Gold medallion architecture** on Delta Lake with PySpark,
  supporting **full, append, and merge (SCD-1 upsert)** load patterns driven by watermarking.
- Engineered **auditing and incremental control** via an Azure SQL `control` schema
  (`table_config`, `watermark`, `audit_log`) with per-stage run logging and failure alerting.
- Applied **Unity Catalog governance** (access connector → storage credential → external location →
  volume) and **Key Vault**-backed secrets; version-controlled ADF and notebooks with **GitHub CI/CD**.
- Stack: Azure Data Factory, Azure Databricks, PySpark, Delta Lake, ADLS Gen2, Azure SQL, Unity
  Catalog, Key Vault, Git.

> Keep to 3–4 bullets on the CV; the block above is the full menu — pick the bullets that match the JD.

---

## LinkedIn — Featured / project description (shorter)

Built a metadata-driven healthcare lakehouse on Azure: ADF ingests PostgreSQL + CSV sources into ADLS
Gen2, and Databricks processes them through a Bronze/Silver/Gold medallion architecture on Delta Lake
— full/append/merge loads, watermark-based incrementals, Unity Catalog governance, Key Vault secrets,
and GitHub CI/CD. Config-driven, so a new table is a row in a control table, not a new pipeline.
Repo + walkthrough 👉 [link]

---

## Interview — the 60-second walkthrough

> "I built a metadata-driven lakehouse to learn the ADF-to-Databricks orchestration flow end to end.
> The core idea is that ingestion is config-driven: every table is a row in a `table_config` control
> table — source system, load type, watermark column, merge keys — so ADF's main pipeline looks up
> the active tables and a ForEach runs an inner pipeline per table, landing data on a timestamped path
> in ADLS. Databricks then takes it through Bronze, Silver and Gold on Delta — Bronze keeps raw plus
> audit columns, Silver cleans, types and dedupes, and applies the load type, with a Delta MERGE for
> upserts, and Gold builds the business marts. I used Unity Catalog for access via an access connector,
> Key Vault for secrets, and Git for CI/CD on both ADF and the notebooks."

### Questions you must be ready for
- **How does the ADLS ↔ Databricks connection work?** → access connector (managed identity) → storage
  credential → external location → external volume. No account keys, no mounts. (See `setup/adls_connection.md`.)
- **Full vs append vs merge — when each?** → full for small dims, append for immutable events, merge
  for slowly-changing entities keyed on `merge_keys`.
- **How do incrementals work?** → `watermark_column` + `control.watermark`; read rows above the last
  watermark, then advance it after a successful load.
- **What's in Bronze that's not in Silver?** → raw fidelity + audit columns (`_ingested_at`,
  `_source_file`); Silver drops those, cleans, types, dedupes.
- **Why metadata-driven?** → scale: onboard a table with a config row, not a code change; one pipeline
  serves many sources.

---

## Do NOT

- Don't imply it was production or client work — it's a personal project on synthetic data. Say that
  plainly; it's still impressive.
- Don't claim tools you didn't actually run (e.g. Kafka/streaming) unless you extend the project to
  include them.
- Do actually run it end to end before you talk about it — you want to have *seen* every error.
