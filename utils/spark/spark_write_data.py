from typing import Dict
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, lit, to_timestamp, when, date_trunc, date_format
from pyspark.sql.types import *

from ELTReportFinance.databases.mongodb_connect import MongoDBConnect


class SparkWriteDatabase:
    def __init__(self, spark : SparkSession, db_configs: Dict):
        self.spark = spark
        self.db_configs = db_configs

    def spark_write_mongodb(self, df : DataFrame, uri : str, database : str, collection : str, mode : str = "append"):
        df.write\
            .format("mongo") \
            .option("uri", uri) \
            .option("database", database) \
            .option("collection", collection) \
            .mode(mode) \
            .save()

        print(f"------spark write data to mongodb successfully----")

    def spark_validate_mongodb(self, df_write : DataFrame, uri : str, database: str, collection: str):
        try:
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
            df_read = self.spark.read \
                .format("mongo") \
                .option("uri", uri) \
                .option("database", database) \
                .option("collection", collection) \
                .option("pipeline", '[{ "$match": { "spark_temp": "spark_write" } }]') \
                .load()

            # df_read.show()
            # df_with_timestamp = df_read.withColumn(
            #     "updated_at",
            #     when(col("updated_at").isNull() | (col("updated_at") == "null"), lit(None).cast(TimestampType()))
            #     .when(col("updated_at").isNotNull() & (col("updated_at") != "null"),
            #           to_timestamp(col("updated_at"), "yyyy-MM-dd HH:mm:ss"))
            # )

            df_with_timestamp = df_read \
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
                col("status_download"),
                col("status_uploaded"),
                col("status_extracted"),
                col("status_transformed"),
                # col("status"),
                # date_format("created_at", "yyyy-MM-dd HH:mm:ss.SSS").alias("created_at"),
                # date_format("updated_at", "yyyy-MM-dd HH:mm:ss.SSS").alias("updated_at"),
                col("created_at"),
                col("updated_at"),
                col("spark_temp")
                )
            df_with_timestamp.show(truncate=False)
            df_with_timestamp.printSchema()
            df_temp = df_write.exceptAll(df_with_timestamp)
            print(df_temp.count())
            if df_temp.count() != 0:
                df_temp.write \
                    .format("mongo") \
                    .option("uri", uri) \
                    .option("database", database) \
                    .option("collection", collection) \
                    .mode("append") \
                    .save()

                print(f"------spark write missing data to mongodb successfully----")

            try:
                with MongoDBConnect(uri, database) as mongodb_client:
                    mongodb_client.db.repositories.update_many({}, {"$unset": {"spark_temp": "spark_write"}})
            except Exception as e:
                raise Exception(f"-----failed to connect to mongodb: {e}------")

            print(f"--------validate spark write data to mongodb collection {collection} successfully-------")

        except Exception as e:
            raise Exception(f"-----Failed to write missing records to mongodb: {e}---") from e
