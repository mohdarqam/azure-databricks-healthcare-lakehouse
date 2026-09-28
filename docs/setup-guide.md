# Setup guide

A step-by-step build. Everything here runs on **free tiers** (Azure free account with $200 credit,
Neon free Postgres, Azure SQL free offer). Estimated time: a focused day.

> Replace every placeholder in `<angle brackets>`. Never commit real passwords — use Key Vault.

## Prerequisites

- An Azure account (free trial is fine). Portal: <https://portal.azure.com>
- Basic familiarity with Azure Data Factory (linked services, datasets, pipelines).
- A GitHub account.

---

## Step 1 — Resource group

Create one resource group to hold everything, e.g. `rg-healthcare-lakehouse`, in a region close to you.

## Step 2 — Source A: Neon PostgreSQL

1. Sign up at <https://neon.tech> (free) and create a project, e.g. `meridian-health`.
2. Open the SQL editor and run [`../sql/postgres/01_create_source_tables.sql`](../sql/postgres/01_create_source_tables.sql).
3. From **Connect**, copy the host, database, user and password — you'll need them for the ADF linked service.

## Step 3 — Source B + Landing: ADLS Gen2

1. Create a **Storage account**. On the *Advanced* tab, enable **Hierarchical namespace** (this makes
   it ADLS Gen2, not plain blob).
2. Create two containers: `source` (drop the partner CSVs here) and `landing` (pipeline output).
3. Upload the sample CSVs from [`../data/sample/`](../data/sample/) into `source/`.

## Step 4 — Metadata DB: Azure SQL

1. Create an **Azure SQL Database** using the **free offer**, with a new server.
2. Choose SQL authentication and note the admin user/password.
3. Under the SQL **server** → *Networking*, add a firewall rule allowing your client (and, for the demo,
   ADF). Run [`../sql/azure-sql/02_create_control_tables.sql`](../sql/azure-sql/02_create_control_tables.sql).

## Step 5 — Key Vault

1. Create a **Key Vault**.
2. Grant yourself the *Key Vault Administrator* role (Access control → Add role assignment → your user).
3. Add secrets: `postgres-password` and `metadata-db-password`.

## Step 6 — Azure Data Factory

1. Create a **Data Factory (V2)** and *Launch Studio*.
2. In **Manage → Git configuration**, connect a GitHub repo (e.g. `healthcare-lakehouse-adf`).
3. Create linked services:
   - **PostgreSQL** — host/db/user from Step 2; password **from Key Vault**.
   - **ADLS Gen2** — system-assigned managed identity; grant ADF the *Storage Blob Data Contributor*
     role on the storage account.
   - **Azure SQL Database** — the metadata DB; password from Key Vault.
   - **Key Vault** — so the above can resolve secrets.
4. Build the two pipelines per [`../adf/README.md`](../adf/README.md).

## Step 7 — Databricks

1. Create an **Azure Databricks** workspace (workspace type: *hybrid*, so you can use an all-purpose
   cluster and your own storage).
2. Create a small **all-purpose cluster** (single node is enough on free credits; disable Photon to
   save cost).
3. Connect Databricks to GitHub (Settings → Linked accounts) and create a **Git folder** for your
   notebooks repo.
4. Set up the ADLS connection (credential → external location → volume) following
   [`../databricks/setup/adls_connection.md`](../databricks/setup/adls_connection.md).
5. Run the notebooks in order:
   - [`../databricks/notebooks/landing_to_bronze.py`](../databricks/notebooks/landing_to_bronze.py)
   - [`../databricks/notebooks/bronze_to_silver.py`](../databricks/notebooks/bronze_to_silver.py)
   - [`../databricks/notebooks/silver_to_gold.py`](../databricks/notebooks/silver_to_gold.py)

## Step 8 — Run end to end

1. Trigger `pl_source_to_silver_main` with `source_system = postgres`, then again with `adls_csv`.
2. Confirm landing folders appear with timestamped parquet.
3. Run the medallion notebooks; confirm bronze/silver/gold Delta tables populate.
4. Check `control.audit_log` for one success row per stage.

## Cost hygiene

- Set the cluster to auto-terminate (e.g. 30–60 min).
- Stop/delete resources when you're done for the day; the resource group makes cleanup one click.
