import os
import sys

# Set environment variables
os.environ['PYSPARK_PYTHON'] = sys.executable
os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable

from pyspark.sql import SparkSession

# Create Spark session with updated MongoDB connector configuration
spark = SparkSession.builder \
    .appName("MongoDB_JSON_Reader") \
    .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:10.2.1") \
    .config("spark.mongodb.input.uri", "mongodb://localhost:27017/AmazonReviewer.AmazondReview_Customers") \
    .config("spark.driver.memory", "4g") \
    .config("spark.executor.memory", "4g") \
    .master("local[*]") \
    .getOrCreate()

try:
    # Read from MongoDB with updated syntax
    df = spark.read \
        .format("com.mongodb.spark.sql.DefaultSource") \
        .option("uri", "mongodb://localhost:27017/AmazonReviewer.AmazondReview_Customers") \
        .load()

    # Show the first 20 records
    print("\nFirst 20 records from the dataset:")
    df.show(20, truncate=False)

    # Print schema
    print("\nDataset Schema:")
    df.printSchema()

except Exception as e:
    print(f"Error occurred: {str(e)}")
    import traceback
    traceback.print_exc()
    
finally:
    # Stop Spark session
    spark.stop()