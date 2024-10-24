import os
import sys
from pyspark import SparkConf, SparkContext
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("Breweries_Gold").getOrCreate()

df_spark_breweries_silver = spark.read.parquet("/usr/local/datalake/silver/openbrewerydb/breweries/breweries_parquet")

df_spark_breweries_silver.createOrReplaceTempView("breweries_agg")

df_spark_breweries_gold = spark.sql("""
    SELECT
        country,
        brewery_type,
        count(*) as breweries_cnt
    FROM breweries
    GROUP BY country,
             brewery_type
    ORDER BY country,
             brewery_type
""")

df_spark_breweries_gold.write \
    .format("parquet") \
    .mode("overwrite") \
    .save("/usr/local/datalake/gold/breweries/vw_breweries_by_location_and_type")
