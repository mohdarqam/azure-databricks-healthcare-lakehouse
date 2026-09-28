# Databricks notebook source
# =============================================================================
# landing_to_bronze
# Reads the latest landing files for a table and writes a Bronze Delta table,
# adding ingestion audit columns. Raw fidelity is preserved — no business logic.
#
# Parameters (Databricks widgets, or passed from an ADF Databricks job):
#   catalog        e.g. "healthcare"
#   source_system  e.g. "postgres"
#   table_name     e.g. "patients"
#   bronze_table   e.g. "bronze_patients"
#   file_format    "parquet" | "csv"
# =============================================================================
from pyspark.sql import functions as F

dbutils.widgets.text("catalog", "healthcare")
dbutils.widgets.text("source_system", "postgres")
dbutils.widgets.text("table_name", "patients")
dbutils.widgets.text("bronze_table", "bronze_patients")
dbutils.widgets.text("file_format", "parquet")

catalog       = dbutils.widgets.get("catalog")
source_system = dbutils.widgets.get("source_system")
table_name    = dbutils.widgets.get("table_name")
bronze_table  = dbutils.widgets.get("bronze_table")
file_format   = dbutils.widgets.get("file_format")

bronze_schema = "bronze"
landing_root  = f"/Volumes/{catalog}/landing/landing_volume/{source_system}/{table_name}"

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{bronze_schema}")

# --- pick the most recent timestamped folder for this table ----------------
folders = [f.path for f in dbutils.fs.ls(landing_root)]
if not folders:
    raise Exception(f"No landing data found under {landing_root}")
latest_folder = sorted(folders)[-1]   # folders are yyyyMMdd_HHmmss, so lexical sort = chronological
print(f"Reading latest landing folder: {latest_folder}")

# --- read raw ---------------------------------------------------------------
reader = spark.read.format(file_format)
if file_format == "csv":
    reader = reader.option("header", "true").option("inferSchema", "true")
raw_df = reader.load(latest_folder)

# --- add ingestion audit columns -------------------------------------------
bronze_df = (
    raw_df
    .withColumn("_ingested_at", F.current_timestamp())
    .withColumn("_source_system", F.lit(source_system))
    .withColumn("_source_file", F.input_file_name())
    .withColumn("_batch_folder", F.lit(latest_folder))
)

# --- write bronze (overwrite: bronze mirrors the latest landing snapshot) ----
target = f"{catalog}.{bronze_schema}.{bronze_table}"
(bronze_df.write
    .format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(target))

count = spark.table(target).count()
print(f"Bronze written: {target} ({count} rows)")
dbutils.notebook.exit(str(count))
