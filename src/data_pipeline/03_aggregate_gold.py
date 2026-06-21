from pyspark.sql.functions import count, sum, avg, max, round

# 1. Read from the clean, structured Silver layer
silver_df = spark.read.table("portfolio_catalog.compliance_project.paysim_silver")

# 2. Aggregate individual transactions into entity-level Risk Profiles
gold_risk_profiles = silver_df.groupBy("originator_id").agg(
    
    # Volume & Velocity Metrics
    count("*").alias("total_transactions"),
    round(sum("amount"), 2).alias("total_volume_moved"),
    round(avg("amount"), 2).alias("avg_tx_size"),
    
    # Behavioral Risk Indicators (Using the features we built in Silver)
    sum("is_high_risk_tx_type").alias("high_risk_tx_count"),
    
    # Ledger Integrity Metrics
    round(sum("orig_balance_discrepancy"), 2).alias("total_discrepancy_amount"),
    
    # Historical System Flags
    max("is_system_flagged").alias("has_prior_system_flags")
    
).withColumnRenamed("originator_id", "account_id") # Rename to match standard CRM/Audit terminology

# 3. Write to the Gold Layer
gold_risk_profiles.write.format("delta") \
    .mode("overwrite") \
    .saveAsTable("portfolio_catalog.compliance_project.customer_risk_profiles")

print("Gold Customer Risk Profiles generated successfully.")