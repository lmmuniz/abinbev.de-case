import os
import sys
from pyspark.sql.functions import input_file_name
from pyspark.sql.window import Window
from pyspark.sql import functions as F
from pyspark import SparkConf, SparkContext
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("Breweries_Silver").getOrCreate()

df_spark_breweries = spark.read.json('/usr/local/datalake/bronze/openbrewerydb/breweries/')

df_spark_breweries = df_spark_breweries.withColumn("source_file_name", input_file_name())

df_spark_breweries.createOrReplaceTempView("breweries")

df_spark_dedup_breweries = spark.sql("""
    with dedup as (
        SELECT
            *,
            ROW_NUMBER() OVER (PARTITION BY id ORDER BY source_file_name DESC) as rn
        FROM breweries
    )
    SELECT *
    FROM dedup
    WHERE rn = 1
""")

df_spark_dedup_breweries = df_spark_dedup_breweries.drop("rn")

df_spark_dedup_breweries.write \
    .format("parquet") \
    .mode("overwrite") \
    .partitionBy("country", "state") \
    .save("/usr/local/datalake/silver/openbrewerydb/breweries/breweries_parquet")
