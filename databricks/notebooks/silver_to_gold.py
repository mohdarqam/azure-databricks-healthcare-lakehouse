# Databricks notebook source
# =============================================================================
# silver_to_gold
# Builds a business-ready GOLD table: a patient-360 mart joining patients to
# their hospital and primary doctor, plus a small KPI aggregate. This is where
# analysts / dashboards / Genie actually read from.
#
# Parameters:
#   catalog   e.g. "healthcare"
# =============================================================================
from pyspark.sql import functions as F

dbutils.widgets.text("catalog", "healthcare")
catalog = dbutils.widgets.get("catalog")

gold_schema = "gold"
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{gold_schema}")

patients  = spark.table(f"{catalog}.silver.silver_patients")
doctors   = spark.table(f"{catalog}.silver.silver_doctors")
hospitals = spark.table(f"{catalog}.silver.silver_hospitals")

# --- gold_patient_360 -------------------------------------------------------
patient_360 = (
    patients.alias("p")
    .join(hospitals.alias("h"), F.col("p.hospital_id") == F.col("h.hospital_id"), "left")
    .join(doctors.alias("d"), F.col("p.primary_doctor_id") == F.col("d.doctor_id"), "left")
    .select(
        F.col("p.patient_id"),
        F.col("p.full_name").alias("patient_name"),
        F.col("p.date_of_birth"),
        (F.floor(F.datediff(F.current_date(), F.col("p.date_of_birth")) / 365.25)).alias("age"),
        F.col("p.gender"),
        F.col("h.hospital_name"),
        F.col("h.county"),
        F.col("d.full_name").alias("primary_doctor"),
        F.col("d.speciality").alias("doctor_speciality"),
        F.current_timestamp().alias("_gold_loaded_at"),
    )
)

(patient_360.write.format("delta").mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(f"{catalog}.{gold_schema}.gold_patient_360"))

# --- gold_hospital_kpis (example aggregate for the dashboard) ---------------
hospital_kpis = (
    patient_360.groupBy("hospital_name", "county")
    .agg(
        F.countDistinct("patient_id").alias("patient_count"),
        F.round(F.avg("age"), 1).alias("avg_patient_age"),
        F.countDistinct("primary_doctor").alias("active_doctors"),
    )
    .orderBy(F.col("patient_count").desc())
)

(hospital_kpis.write.format("delta").mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(f"{catalog}.{gold_schema}.gold_hospital_kpis"))

print("Gold written: gold_patient_360, gold_hospital_kpis")
display(hospital_kpis)
