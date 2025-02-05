import gzip
import json
from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017')
db = client['AmazonReviewer']
collection = db['AmazondReview_Customers']

# Open the .gz file in text mode and process line by line
with gzip.open('D:/All_Amazon_Review.json.gz', 'rt', encoding='utf-8') as f:
    batch = []
    for line in f:
        try:
            # Load each line as a JSON document
            data = json.loads(line)
            batch.append(data)
            
            # If batch size reaches 1000, insert into MongoDB
            if len(batch) >= 1000:
                collection.insert_many(batch)
                batch.clear()  # Clear batch for the next set of documents

        except json.JSONDecodeError as e:
            print(f"Error decoding line: {e}")
    
    # Insert any remaining data in the batch after finishing the loop
    if batch:
        collection.insert_many(batch)

print("Data Imported Successfully!")
