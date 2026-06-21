from pyspark.sql.types import StructType, StructField, IntegerType, StringType, DoubleType

# 1. Define the strict, formal enterprise schema
paysim_schema = StructType([
    StructField("step", IntegerType(), nullable=False),
    StructField("type", StringType(), nullable=False),
    StructField("amount", DoubleType(), nullable=False),
    StructField("nameOrig", StringType(), nullable=True),
    StructField("oldbalanceOrg", DoubleType(), nullable=True),
    StructField("newbalanceOrig", DoubleType(), nullable=True),
    StructField("nameDest", StringType(), nullable=True),
    StructField("oldbalanceDest", DoubleType(), nullable=True),
    StructField("newbalanceDest", DoubleType(), nullable=True),
    StructField("isFraud", IntegerType(), nullable=True),
    StructField("isFlaggedFraud", IntegerType(), nullable=True)
])

# 2. Apply the schema directly upon reading the raw CSV
raw_csv_path = "/Volumes/portfolio_catalog/compliance_project/raw_data/paysim_raw.csv"

raw_df = spark.read.csv(
    raw_csv_path, 
    schema=paysim_schema, # Enforces our strict StructType instantly
    header=True
)

# 3. Save to Bronze
raw_df.write.format("delta") \
    .mode("overwrite") \
    .saveAsTable("portfolio_catalog.compliance_project.paysim_bronze")

print("Strictly-typed Bronze table created successfully.")