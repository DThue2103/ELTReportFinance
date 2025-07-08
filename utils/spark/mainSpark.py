import pandas as pd
from pyspark.sql.functions import col, from_json, lit
from pyspark.sql.types import *

from ELTReportFinance1.config.spark_config import SparkConnect
from ELTReportFinance1.config.database_config import get_spark_config
from ELTReportFinance1.utils.spark.spark_write_data import SparkWriteDatabase

def main():
    jars = [
        "org.mongodb.spark:mongo-spark-connector_2.12:3.0.1"
    ]
    #create spark context
    spark_connect = SparkConnect(
        app_name="ReportFinance",
        master_url="local[*]",
        executor_memory="4g",
        executor_cores="2",
        driver_memory="2g",
        jar_packages=jars,
        log_level="INFO"
    )
    #create schema
    schema = StructType([
        StructField("id_group", IntegerType(), True),
        StructField("company_name", StringType(), True),
        StructField("stock_code", StringType(), True),
        StructField("year", IntegerType(), True),
        StructField("quarter", IntegerType(), True),
        StructField("report_type", StringType(), True),
        StructField("file_format", StringType(), True),
        StructField("file_name", StringType(), True),
        StructField("source_url", StringType(), True),
        StructField("local_path", StringType(), True),
        StructField("minio_path", StringType(), True),
        StructField("status", StructType([
            StructField("download", BooleanType(), True),
            StructField("uploaded", BooleanType(), True),
            StructField("extracted", BooleanType(), True),
            StructField("transformed", BooleanType(), True)
        ]), True),
        StructField("created_at", TimestampType(), True),
        StructField("updated_at", TimestampType(), True)
    ])

    df = spark_connect.spark.read.option("multiLine", True) .schema(schema).json(r"/home/huedt/Documents/PythonProjects/ELTReportFinance1/data/uploaded_record_finance_report.json")

    df_write_table = df.withColumn("spark_temp", lit("spark_write")) \
        .select(
        col("id_group"),
        col("company_name"),
        col("stock_code"),
        col("year"),
        col("quarter"),
        col("report_type"),
        col("file_format"),
        col("file_name"),
        col("source_url"),
        col("local_path"),
        col("minio_path"),
        col("status.download").alias("status_download"),
        col("status.uploaded").alias("status_uploaded"),
        col("status.extracted").alias("status_extracted"),
        col("status.transformed").alias("status_transformed"),
        # col("status"),
        col("created_at"),
        col("updated_at"),
        col("spark_temp")
    )
    # df_write_table.show()
    df_write_table.printSchema()
    spark_config = get_spark_config()
    # print(spark_config)
    df_write = SparkWriteDatabase(spark_connect.spark, spark_config)
    df_write.spark_write_mongodb(df_write_table, spark_config["mongodb"]["uri"], spark_config["mongodb"]["database"], spark_config["mongodb"]["collection"])
    df_write.spark_validate_mongodb(df_write_table, spark_config["mongodb"]["uri"], spark_config["mongodb"]["database"], spark_config["mongodb"]["collection"])

if __name__ == '__main__':
    main()