# Apache-Spark-Data-Loading
- Using Amazon Review Data Analysis 

## Overview
This project implements large-scale data processing of Amazon Review dataset using Apache Spark and MongoDB. The implementation provides two approaches:
- MongoDB pipeline: Data loaded to MongoDB first, then processed via PySpark
- Direct JSON processing: Data processed directly from JSON files using PySpark

## Prerequisites
- Python 3.8+
- Java 8/11
- Apache Spark 3.4.0
- MongoDB 6.0+
- WinUtils (for Windows users)

## Environment Setup

### 1. System Environment Variables
Add the following to system environment variables:
```
JAVA_HOME=C:\Program Files\Java\jdk1.8.0_xxx
SPARK_HOME=C:\spark-3.4.0-bin-hadoop3
HADOOP_HOME=C:\hadoop
PATH=%PATH%;%SPARK_HOME%\bin;%HADOOP_HOME%\bin
```

### 2. WinUtils Setup (Windows Only)
1. Download winutils.exe
2. Place in `C:\hadoop\bin\`
3. Verify with: `winutils.exe chmod -R 777 C:\tmp\hive`

### 3. Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
```

### 4. Dependencies
```bash
pip install pyspark pymongo
```

## Project Structure
```
project/
├── pymongo_script.py      # MongoDB data loading
├── fetch_mongo.py         # Data retrieval from MongoDB
├── readingjson.py         # Direct JSON processing
├── logs/
└── data/
```

## Data Processing Approaches

### Approach 1: MongoDB Pipeline
1. Load data to MongoDB:
```python
python pymongo_script.py
```
2. Process data using PySpark:
```python
python fetch_mongo.py
```

### Approach 2: Direct JSON Processing
```python
python readingjson.py
```

## Known Issues and Solutions

1. File Path Escape Sequence
- Issue: Windows path separators causing errors
- Solution: Use raw strings (r"path") or forward slashes

2. Duplicate Columns
- Issue: Schema inference creating duplicate column names
- Solution: Explicit schema definition in PySpark

3. Malformed Records
- Issue: JSON parsing errors
- Solution: Using permissive mode in Spark reader
```python
df = spark.read.json(path, mode="PERMISSIVE")
```

## Error Handling
- Implemented try-catch blocks for MongoDB operations
- Used Spark's built-in error handling for malformed records
- Logging implemented for tracking issues

## Performance Optimization
- Configured proper partition sizes
- Implemented batch processing for MongoDB operations
- Memory optimization via Spark configurations

## Usage Notes
1. Ensure sufficient disk space (80GB+) for uncompressed data
2. Monitor MongoDB memory usage during initial load
3. Adjust Spark memory settings based on available RAM

## Troubleshooting
1. MongoDB Connection Issues:
```bash
mongod --dbpath /path/to/data
```

2. Spark Memory Issues:
```python
spark.conf.set("spark.driver.memory", "4g")
spark.conf.set("spark.executor.memory", "4g")
```

## Contributors
- Zaib Un Nisa 21i-0383
- Aiman Karim 21i-0664
  
