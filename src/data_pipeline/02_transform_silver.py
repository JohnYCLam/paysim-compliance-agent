from pyspark.sql.functions import col, current_timestamp, when, abs, trim, upper

# Read from the strictly-typed Bronze layer
bronze_df = spark.read.table("portfolio_catalog.compliance_project.paysim_bronze")

# 1. Standardization & Renaming (No casting needed!)
df_standardized = bronze_df.select(
    col("step"),
    trim(upper(col("type"))).alias("tx_type"), 
    col("amount"),
    trim(col("nameOrig")).alias("originator_id"),
    col("oldbalanceOrg").alias("old_balance_orig"), # Fixing the CSV typo
    col("newbalanceOrig").alias("new_balance_orig"),
    trim(col("nameDest")).alias("beneficiary_id"),
    col("oldbalanceDest").alias("old_balance_dest"),
    col("newbalanceDest").alias("new_balance_dest"),
    col("isFraud").alias("is_actual_fraud"),
    col("isFlaggedFraud").alias("is_system_flagged")
)

# 2. Compliance Integrity Filters
df_filtered = df_standardized.filter(
    (col("amount") >= 0) & 
    col("originator_id").isNotNull() & 
    col("beneficiary_id").isNotNull() &
    (col("originator_id") != "") &
    (col("beneficiary_id") != "")
)

# 3. Derived Audit Features for the LangGraph Agent
silver_df = df_filtered.withColumn(
    "orig_balance_discrepancy", 
    abs((col("old_balance_orig") - col("amount")) - col("new_balance_orig"))
).withColumn(
    "is_high_risk_tx_type",
    when(col("tx_type").isin("TRANSFER", "CASH_OUT"), 1).otherwise(0)
).withColumn(
    "ingested_at", current_timestamp()
)

# 4. Deterministic Deduplication
silver_df = silver_df.dropDuplicates(["step", "originator_id", "beneficiary_id", "amount", "tx_type"])

# Write to Silver Layer
silver_df.write.format("delta") \
    .mode("overwrite") \
    .saveAsTable("portfolio_catalog.compliance_project.paysim_silver")

print("Business logic applied and Silver table updated successfully.")