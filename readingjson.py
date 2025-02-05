import os
import time
import psutil
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, year, month, to_timestamp, count, when, desc

class ReviewsProcessor:
    def __init__(self, input_path, log_path="processing_logs"):
        self.input_path = input_path
        self.log_path = log_path
        self.start_time = None
        self.spark = None
        self.df = None
        os.makedirs(log_path, exist_ok=True)
        self.log_file = os.path.join(
            log_path, 
            f"processing_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )

    def log_message(self, message):
        print(message)
        with open(self.log_file, "a") as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

    def initialize_spark(self):
        self.log_message("Initializing Spark session...")
        
        self.spark = SparkSession.builder \
            .appName("Amazon_Reviews_Processor") \
            .master("local[*]") \
            .config("spark.driver.memory", "4g") \
            .config("spark.sql.legacy.timeParserPolicy", "LEGACY") \
            .config("spark.sql.caseSensitive", "true") \
            .config("spark.sql.legacy.allowDuplicateFieldNames", "true") \
            .getOrCreate()

        self.spark.sparkContext.setLogLevel("WARN")

    def load_data(self):
        self.log_message("Starting data loading...")
        self.start_time = time.time()

        # Read the JSON file with permissive mode
        raw_df = self.spark.read \
            .option("compression", "gzip") \
            .option("mode", "PERMISSIVE") \
            .option("columnNameOfCorruptRecord", "_corrupt_record") \
            .json(self.input_path)

        # List all columns and handle duplicates
        columns = raw_df.columns
        self.log_message(f"\nOriginal columns found: {len(columns)}")
        
        # Create a mapping for renamed columns
        column_mapping = {}
        seen_columns = set()
        
        for col_name in columns:
            base_name = col_name.replace(':', '_').replace(' ', '_').lower()
            if base_name in seen_columns:
                counter = 1
                while f"{base_name}_{counter}" in seen_columns:
                    counter += 1
                new_name = f"{base_name}_{counter}"
            else:
                new_name = base_name
            seen_columns.add(new_name)
            column_mapping[col_name] = new_name

        # Apply the column renaming
        self.df = raw_df
        for old_name, new_name in column_mapping.items():
            self.df = self.df.withColumnRenamed(old_name, new_name)

        # Show the first few rows to verify structure
        self.log_message("\nFirst few rows after column renaming:")
        self.df.show(5, truncate=False)

        # Get record count
        total_records = self.df.count()
        load_time = time.time() - self.start_time
        self.log_message(f"\nData loading completed.")
        self.log_message(f"Total records: {total_records:,}")
        self.log_message(f"Loading time: {load_time:.2f} seconds")

    def analyze_data(self):
        self.log_message("\nAnalyzing data...")
        
        # Show schema
        self.log_message("\nFinal Schema:")
        self.df.printSchema()
        
        # Basic counts
        total_records = self.df.count()
        self.log_message(f"\nTotal records: {total_records:,}")
        
        # Null value analysis for main fields
        main_fields = ['asin', 'overall', 'review_text', 'reviewer_id', 'summary']
        
        self.log_message("\nNull value analysis for main fields:")
        for field in main_fields:
            if field in self.df.columns:
                null_count = self.df.filter(col(field).isNull()).count()
                percentage = (null_count / total_records) * 100
                self.log_message(f"{field}: {null_count:,} nulls ({percentage:.2f}%)")

    def run(self):
        try:
            self.initialize_spark()
            self.load_data()
            self.analyze_data()
            
        except Exception as e:
            self.log_message(f"\nError occurred: {str(e)}")
            import traceback
            self.log_message(traceback.format_exc())
            
        finally:
            if self.spark:
                self.spark.stop()
                self.log_message("Spark session stopped")

if __name__ == "__main__":
    processor = ReviewsProcessor(
        input_path=r"D:\All_Amazon_Review.json.gz",
        log_path="amazon_reviews_logs"
    )
    processor.run()