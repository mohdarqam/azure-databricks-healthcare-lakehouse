# Metadata-Driven Healthcare Lakehouse on Azure & Databricks

An end-to-end, **metadata-driven** data engineering platform that ingests healthcare data
from multiple sources, lands it in ADLS Gen2, and processes it through a **Bronze → Silver → Gold
medallion architecture** using Azure Data Factory (orchestration) and Azure Databricks (transformation),
with governance in Unity Catalog and CI/CD through GitHub.

> **Domain:** *Meridian Health Network* — a fictional group of hospitals used to model a realistic
> healthcare data estate (patients, doctors, hospitals, lab results, insurance providers).
> Rename this to your own fictional entity if you fork it.

---

## Why this project exists

Healthcare data lives in scattered systems — hospital databases, lab partners, insurance feeds —
and combining it is usually manual, slow, and error-prone. This project builds a repeatable,
config-driven pipeline so that **adding a new table is a row in a control table, not a new pipeline**.

It demonstrates the skills a modern Data Engineer is hired for:

- Metadata / config-driven ingestion (scale without rebuilding pipelines)
- Incremental loads (full / append / merge with watermarking)
- Medallion architecture on Delta Lake
- Cloud-native orchestration and secrets management
- Governance with Unity Catalog
- CI/CD for both ADF and Databricks

---

## Architecture

```
                          ┌─────────────────────────────────────────────┐
   SOURCES                │              INGESTION (ADF)                  │
 ┌──────────────┐         │   Lookup active tables ─► ForEach ─► Copy     │
 │ PostgreSQL   │────────►│   (driven by control.table_config)           │
 │ (Neon)       │         │   dynamic path: source/table/timestamp       │
 ├──────────────┤         └───────────────────────┬─────────────────────┘
 │ ADLS CSV     │────────►                         │  Parquet / CSV
 │ (partners)   │                                  ▼
 └──────────────┘                     ┌────────────────────────┐
                                      │   LANDING (ADLS Gen2)  │
                                      └───────────┬────────────┘
                                                  │  Databricks (PySpark + Delta)
                          ┌───────────────────────┼───────────────────────┐
                          ▼                       ▼                        ▼
                    ┌──────────┐            ┌──────────┐             ┌──────────┐
                    │  BRONZE  │  raw+audit │  SILVER  │ cleaned/    │   GOLD   │ business
                    │  Delta   │───────────►│  Delta   │ conformed  ─►│  Delta   │ marts / KPIs
                    └──────────┘            └──────────┘             └──────────┘
                                                                          │
   GOVERNANCE: Unity Catalog   |   SECRETS: Key Vault   |   CONSUMPTION:  ▼ dashboards / Genie
   AUDIT + METADATA: Azure SQL (control.table_config, watermark, audit_log)
   ORCHESTRATION: ADF pipelines   |   CI/CD: GitHub (ADF + Databricks repos)
```

Full detail in [`docs/architecture.md`](docs/architecture.md).

---

## Tech stack

| Layer | Technology |
|---|---|
| Sources | PostgreSQL (Neon, free tier), CSV on ADLS Gen2 |
| Ingestion / Orchestration | Azure Data Factory (metadata-driven, dynamic content) |
| Storage | Azure Data Lake Storage Gen2 (Parquet, Delta) |
| Transformation | Azure Databricks, PySpark, Delta Lake |
| Metadata / Audit | Azure SQL Database (`control` schema) |
| Governance | Unity Catalog (external locations, volumes, credentials) |
| Secrets | Azure Key Vault (linked to ADF; secret scopes in Databricks) |
| CI/CD | GitHub integration for ADF and Databricks |
| Consumption | Databricks SQL dashboard, Genie (NL queries) |

---

## Repository layout

```
.
├── README.md
├── docs/
│   ├── architecture.md            # Deep dive: layers, load types, folder structure
│   ├── setup-guide.md             # Step-by-step build (Azure + Neon + Databricks)
│   ├── add-to-resume.md           # How to describe this on CV / LinkedIn / interview
│   └── portfolio-plan.md          # Turning this into a portfolio piece
├── sql/
│   ├── postgres/
│   │   └── 01_create_source_tables.sql     # patients, doctors, hospitals + sample data
│   └── azure-sql/
│       └── 02_create_control_tables.sql    # table_config, watermark, audit_log + seed rows
├── adf/
│   └── README.md                  # Pipeline design: main + inner, lookup, forEach, copy, dynamic paths
├── databricks/
│   ├── setup/
│   │   └── adls_connection.md      # Credential → external location → volume (interview favourite)
│   └── notebooks/
│       ├── landing_to_bronze.py
│       ├── bronze_to_silver.py
│       └── silver_to_gold.py
├── data/sample/                   # Sample CSVs for the partner (ADLS CSV) source
├── .github/workflows/             # CI stubs
├── .gitignore
└── LICENSE
```

---

## Quick start

1. **Sources** — create a free Neon PostgreSQL instance and an ADLS Gen2 storage account.
   Run [`sql/postgres/01_create_source_tables.sql`](sql/postgres/01_create_source_tables.sql).
2. **Metadata DB** — create an Azure SQL Database and run
   [`sql/azure-sql/02_create_control_tables.sql`](sql/azure-sql/02_create_control_tables.sql).
3. **ADF** — build the metadata-driven pipelines per [`adf/README.md`](adf/README.md); store the
   Postgres and SQL passwords in Key Vault.
4. **Databricks** — set up the ADLS connection per
   [`databricks/setup/adls_connection.md`](databricks/setup/adls_connection.md), then run the three
   medallion notebooks in order.

Full walkthrough: [`docs/setup-guide.md`](docs/setup-guide.md).

---

## What "metadata-driven" means here

Every table this platform ingests is **one row** in `control.table_config`:

| Column | Purpose |
|---|---|
| `source_system` | `postgres` or `adls_csv` — lets one pipeline serve many sources |
| `source_table_name` / `source_path` | where to read from |
| `bronze/silver/gold_table_name` | where to write |
| `load_type` | `full`, `append`, or `merge` |
| `watermark_column` | drives incremental reads |
| `merge_keys` | drives upserts for `merge` loads |
| `is_active` | pipeline picks up active rows only |

To onboard a new table you insert a row — you do **not** build a new pipeline. That is the whole point.

---

## Credits & honesty note

The reference architecture (metadata-driven ADF + medallion Databricks on a healthcare use case)
is a widely-taught pattern; this repository is my own implementation, written to learn the ADF ⇄
Databricks orchestration flow end to end. Data is entirely synthetic. See
[`docs/add-to-resume.md`](docs/add-to-resume.md) for how I frame it honestly on my CV.

## License

MIT — see [`LICENSE`](LICENSE).
