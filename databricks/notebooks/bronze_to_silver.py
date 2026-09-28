# Databricks notebook source
# =============================================================================
# bronze_to_silver
# Cleans, types and conforms Bronze into Silver. Applies the load_type:
#   full   -> overwrite Silver
#   append -> append new rows
#   merge  -> Delta MERGE upsert on merge_keys (SCD-1)
#
# Parameters:
#   catalog       e.g. "healthcare"
#   bronze_table  e.g. "bronze_patients"
#   silver_table  e.g. "silver_patients"
#   load_type     "full" | "append" | "merge"
#   merge_keys    comma-separated, e.g. "patient_id"  (only for merge)
#   watermark_col e.g. "updated_at" (only for append/merge dedup ordering)
# =============================================================================
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from delta.tables import DeltaTable

dbutils.widgets.text("catalog", "healthcare")
dbutils.widgets.text("bronze_table", "bronze_patients")
dbutils.widgets.text("silver_table", "silver_patients")
dbutils.widgets.text("load_type", "merge")
dbutils.widgets.text("merge_keys", "patient_id")
dbutils.widgets.text("watermark_col", "updated_at")

catalog       = dbutils.widgets.get("catalog")
bronze_table  = dbutils.widgets.get("bronze_table")
silver_table  = dbutils.widgets.get("silver_table")
load_type     = dbutils.widgets.get("load_type")
merge_keys    = [k.strip() for k in dbutils.widgets.get("merge_keys").split(",") if k.strip()]
watermark_col = dbutils.widgets.get("watermark_col").strip()

silver_schema = "silver"
src = f"{catalog}.bronze.{bronze_table}"
tgt = f"{catalog}.{silver_schema}.{silver_table}"

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{silver_schema}")

# --- read bronze ------------------------------------------------------------
df = spark.table(src)

# --- generic cleaning -------------------------------------------------------
# 1) drop internal bronze audit columns from the business layer
audit_cols = [c for c in df.columns if c.startswith("_")]
df = df.drop(*audit_cols)

# 2) trim strings and turn blanks into nulls
for c, t in df.dtypes:
    if t == "string":
        df = df.withColumn(c, F.when(F.trim(F.col(c)) == "", None).otherwise(F.trim(F.col(c))))

# 3) deduplicate: keep the latest row per key when we have keys + a watermark
if merge_keys and watermark_col and watermark_col in df.columns:
    w = Window.partitionBy(*merge_keys).orderBy(F.col(watermark_col).desc())
    df = (df.withColumn("_rn", F.row_number().over(w))
            .filter(F.col("_rn") == 1)
            .drop("_rn"))

df = df.withColumn("_silver_loaded_at", F.current_timestamp())

# --- write according to load_type ------------------------------------------
if load_type in ("full", "append"):
    mode = "overwrite" if load_type == "full" else "append"
    (df.write.format("delta").mode(mode)
        .option("mergeSchema", "true").saveAsTable(tgt))

elif load_type == "merge":
    if not merge_keys:
        raise Exception("merge load_type requires merge_keys")
    if not spark.catalog.tableExists(tgt):
        (df.write.format("delta").saveAsTable(tgt))
    else:
        cond = " AND ".join([f"t.{k} = s.{k}" for k in merge_keys])
        (DeltaTable.forName(spark, tgt).alias("t")
            .merge(df.alias("s"), cond)
            .whenMatchedUpdateAll()
            .whenNotMatchedInsertAll()
            .execute())
else:
    raise Exception(f"Unknown load_type: {load_type}")

count = spark.table(tgt).count()
print(f"Silver written: {tgt} (load_type={load_type}, {count} rows)")
dbutils.notebook.exit(str(count))
