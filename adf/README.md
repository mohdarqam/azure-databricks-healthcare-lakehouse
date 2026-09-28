# ADF — metadata-driven ingestion

Two pipelines. The **main** pipeline discovers what to load; the **inner** pipeline loads one table.
This keeps the `ForEach` body small and each table's logic reusable.

---

## Linked services

| Name | Type | Auth |
|---|---|---|
| `ls_postgres` | PostgreSQL | password from Key Vault (`postgres-password`) |
| `ls_adls` | ADLS Gen2 | system-assigned managed identity |
| `ls_azure_sql` | Azure SQL DB | password from Key Vault (`metadata-db-password`) |
| `ls_keyvault` | Azure Key Vault | managed identity |

Grant the ADF managed identity **Storage Blob Data Contributor** on the storage account.

---

## Datasets

| Name | Linked service | Notes |
|---|---|---|
| `ds_postgres_query` | `ls_postgres` | no table hard-coded — table name passed via query |
| `ds_azure_sql` | `ls_azure_sql` | used by both lookup activities |
| `ds_adls_parquet` | `ls_adls` | parameterised `container`, `folder`; Parquet |
| `ds_adls_csv` | `ls_adls` | for the partner CSV source |

Parameterise the sink dataset so the path is dynamic:

- dataset parameters: `container` (string), `folder` (string)
- in *Connection*, set **File system** = `@dataset().container`, **Directory** = `@dataset().folder`

---

## Pipeline 1 — `pl_source_to_silver_main`

**Parameter:** `source_system` (default `postgres`).

1. **Lookup** `read_active_tables`
   - dataset: `ds_azure_sql`, *First row only*: **off** (we need all rows)
   - query:
     ```sql
     SELECT table_id
     FROM control.table_config
     WHERE is_active = 1
       AND stage = 'source_to_silver'
       AND source_system = '@{pipeline().parameters.source_system}'
     ```
   - set **Retry = 2** (free-tier SQL can be cold on first hit).

2. **ForEach** `ingest_all_tables`
   - Items: `@activity('read_active_tables').output.value`
   - leave *Batch count* blank so tables load in parallel.
   - **Inside:** Execute Pipeline → `pl_source_to_silver_inner`, passing
     `table_id = @item().table_id`.

---

## Pipeline 2 — `pl_source_to_silver_inner`

**Parameter:** `table_id` (int).

1. **Lookup** `read_table_details`
   - dataset: `ds_azure_sql`, *First row only*: **on**
   - query (table_id passed dynamically):
     ```sql
     SELECT * FROM control.table_config
     WHERE table_id = @{pipeline().parameters.table_id}
     ```
   - Retry = 2.

2. **Set variable** `start_time` (string)
   - value:
     ```
     @formatDateTime(utcNow(), 'yyyyMMdd_HHmmss')
     ```
   - the milliseconds are dropped on purpose so folder names are clean.

3. **Copy data** `source_to_landing`
   - **Source** (Postgres): `ds_postgres_query`, query =
     ```
     @concat('SELECT * FROM public.',
             activity('read_table_details').output.firstRow.source_table_name)
     ```
     (For a real incremental merge/append you extend this with a
     `WHERE @{watermark_column} > '@{watermark_value}'` clause — see *Incremental* below.)
   - **Sink** (ADLS Parquet): `ds_adls_parquet`
     - `container` = `landing`
     - `folder` =
       ```
       @concat(activity('read_table_details').output.firstRow.source_system, '/',
               activity('read_table_details').output.firstRow.source_table_name, '/',
               variables('start_time'))
       ```

Result path: `landing/postgres/patients/20260928_113045/part-*.parquet`.

---

## Incremental loads (append / merge)

For `append` and `merge` tables:

1. Read the current watermark:
   ```sql
   SELECT watermark_value FROM control.watermark
   WHERE table_id = @{pipeline().parameters.table_id}
   ```
2. Filter the source query to rows newer than that watermark.
3. After a successful copy, update the watermark to the max value just loaded (a **Stored procedure**
   or **Script** activity against `control.watermark`).

The `merge` upsert itself (insert new / update changed on `merge_keys`) happens in the Databricks
bronze→silver notebook using Delta `MERGE`.

---

## Auditing

Wrap each inner run with two Script activities against `control.audit_log`:

- before the copy: insert a row with `status = 'in_progress'`, `start_time = utcNow()`,
  `adf_run_id = @pipeline().RunId`.
- on success: update `status = 'success'`, `records_written = @activity('source_to_landing').output.rowsCopied`,
  `end_time = utcNow()`.
- on failure (red path): update `status = 'failed'` and trigger a **Logic App** to send a summary email.

---

## CI/CD

Connect ADF to GitHub (`Manage → Git configuration`). Every save writes pipeline/dataset/linked-service
JSON to the collaboration branch; *Publish* promotes to the `adf_publish` branch. Review via PRs and
promote across dev/test/prod with parameterised linked services.
