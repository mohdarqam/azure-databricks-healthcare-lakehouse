# Connecting Databricks to ADLS Gen2 (Unity Catalog)

This is a classic interview question: *"How do you set up access between a Databricks workspace and an
ADLS Gen2 account?"* The modern (Unity Catalog) answer is four steps — **no account keys, no mounts**.

```
Access Connector (managed identity)
        │  1. create a storage CREDENTIAL from it
        ▼
Storage Credential ──2. create an EXTERNAL LOCATION (points at an abfss:// path)──►
        │
        ▼  (grant the connector "Storage Blob Data Contributor" on the ADLS account)
External Location ──3. create an external VOLUME on it──► 4. read/write files by volume path
```

## Steps

1. **Find the access connector.** When you create the workspace with a managed resource group, Azure
   creates an *Access Connector for Azure Databricks* there (a managed identity). Copy its **Resource ID**.

2. **Create a storage credential** (Catalog → `+` → Create a credential → *Storage credential*).
   Paste the access connector's Resource ID.

3. **Grant the connector access to ADLS.** On the storage account → *Access control (IAM)* → add role
   assignment → **Storage Blob Data Contributor** → assign to the access connector (managed identity).

4. **Create an external location** (Catalog → `+` → External location) using that credential and the URL:
   ```
   abfss://landing@<storage_account>.dfs.core.windows.net/
   ```
   Test the connection.

5. **Create a schema + external volume** on the workspace's default catalog:
   ```sql
   CREATE SCHEMA IF NOT EXISTS <catalog>.landing;

   CREATE EXTERNAL VOLUME <catalog>.landing.landing_volume
   LOCATION 'abfss://landing@<storage_account>.dfs.core.windows.net/';
   ```

You can now read landing files by their volume path, e.g.:

```python
path = "/Volumes/<catalog>/landing/landing_volume/postgres/patients/20260928_113045/"
dbutils.fs.ls(path)
df = spark.read.format("parquet").load(path)
```

## Why this over mounts / account keys?

- **Governed** — access is centrally managed in Unity Catalog, auditable per grant.
- **No secrets in code** — identity is the access connector, not a key you have to store.
- **Portable** — the same external location backs volumes, external tables and jobs.

> Azure-specific alternative you should also be able to name: **secret scopes backed by Key Vault**
> plus an ADLS Gen2 access pattern, for workspaces not on Unity Catalog. Prefer UC where available.
