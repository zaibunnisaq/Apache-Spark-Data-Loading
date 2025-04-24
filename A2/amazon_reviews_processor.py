import json
import re
import pandas as pd
from datetime import datetime
import os
import argparse

def parse_amazon_meta_txt(file_path, max_samples=None):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    product_blocks = re.split(r'Id:\s+\d+', content)[1:]
    reviews_data = []
    sample_count = 0
    
    for block in product_blocks:
        asin_match = re.search(r'ASIN:\s+(\w+)', block)
        if not asin_match:
            continue
        asin = asin_match.group(1)
        
        title_match = re.search(r'title:\s+(.+)(?:\n|$)', block)
        title = title_match.group(1) if title_match else ""
        
        category_matches = re.findall(r'\|([^|]+)', block)
        categories = [cat.split('[')[0].strip() for cat in category_matches] if category_matches else []
        main_category = categories[0] if categories else "Unknown"
        
        review_blocks = re.findall(r'(\d{4}-\d{1,2}-\d{1,2})\s+cutomer:\s+(\w+)\s+rating:\s+(\d+)\s+votes:\s+(\d+)\s+helpful:\s+(\d+)', block)
        
        for review in review_blocks:
            try:
                date_obj = datetime.strptime(review[0], '%Y-%m-%d')
                timestamp = int(date_obj.timestamp() * 1000)
            except ValueError:
                timestamp = 0
            
            reviews_data.append({
                "rating": float(review[2]),
                "title": "",
                "text": "",
                "images": [],
                "asin": asin,
                "parent_asin": asin,
                "user_id": review[1],
                "timestamp": timestamp,
                "helpful_vote": int(review[4]),
                "verified_purchase": False,
                "category": main_category
            })
            
            sample_count += 1
            if max_samples and sample_count >= max_samples:
                return reviews_data
    
    return reviews_data

def parse_json_reviews(file_path, max_samples=None):
    reviews_data = []
    sample_count = 0
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            try:
                review = json.loads(line.strip())
                try:
                    date_obj = datetime.strptime(review.get('reviewTime', '01 1, 1970'), '%m %d, %Y')
                    timestamp = int(date_obj.timestamp() * 1000)
                except ValueError:
                    timestamp = review.get('unixReviewTime', 0) * 1000 if review.get('unixReviewTime') else 0
                
                helpful_votes = review.get('helpful', [0, 0])[0]
                
                reviews_data.append({
                    "rating": float(review.get('overall', 0)),
                    "title": review.get('summary', ''),
                    "text": review.get('reviewText', ''),
                    "images": [],
                    "asin": review.get('asin', ''),
                    "parent_asin": review.get('asin', ''),
                    "user_id": review.get('reviewerID', ''),
                    "timestamp": timestamp,
                    "helpful_vote": helpful_votes,
                    "verified_purchase": False,
                    "category": "Amazon Instant Video"
                })
                
                sample_count += 1
                if max_samples and sample_count >= max_samples:
                    return reviews_data
            except json.JSONDecodeError:
                continue
    
    return reviews_data

def parse_meta_instant_video_json(file_path, max_samples=None):
    reviews_data = []
    sample_count = 0
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            try:
                meta = json.loads(line.strip())
                asin = meta.get('asin', '')
                category = meta.get('category', 'Amazon Instant Video')
                parent_asin = meta.get('parent_asin', asin)

                reviews_data.append({
                    "rating": None,
                    "title": "",
                    "text": "",
                    "images": meta.get('image', []),
                    "asin": asin,
                    "parent_asin": parent_asin,
                    "user_id": "",
                    "timestamp": 0,
                    "helpful_vote": 0,
                    "verified_purchase": False,
                    "category": category
                })

                sample_count += 1
                if max_samples and sample_count >= max_samples:
                    return reviews_data
            except json.JSONDecodeError:
                continue
    
    return reviews_data

def combine_review_data(*datasets, max_total_samples=None):
    all_reviews = []
    for data in datasets:
        all_reviews.extend(data)

    if max_total_samples and len(all_reviews) > max_total_samples:
        all_reviews = all_reviews[:max_total_samples]
    
    df = pd.DataFrame(all_reviews)
    df['review_id'] = df['user_id'].fillna('') + '_' + df['asin'].fillna('') + '_' + df['timestamp'].astype(str)
    df.drop_duplicates(subset=['review_id'], keep='first', inplace=True)
    df['review_date'] = pd.to_datetime(df['timestamp'], unit='ms', errors='coerce')

    df['category'] = df['category'].apply(lambda x: x.replace("Books", "Books & Literature") if 'Book' in str(x) else x)
    df['category'] = df['category'].apply(lambda x: "Video & Entertainment" if x == "Amazon Instant Video" else x)

    df.drop('review_id', axis=1, inplace=True)
    return df

def save_combined_data(df, output_path, format='csv'):
    if format.lower() == 'csv':
        df.to_csv(output_path, index=False)
    elif format.lower() == 'json':
        df.to_json(output_path, orient='records', indent=2)
    elif format.lower() == 'excel':
        df.to_excel(output_path, index=False)
    else:
        raise ValueError(f"Unsupported output format: {format}")

def main():
    parser = argparse.ArgumentParser(description='Process Amazon review data from multiple sources.')
    parser.add_argument('--txt', default='amazon-meta.txt', help='Path to amazon-meta.txt file')
    parser.add_argument('--json_reviews', default='reviews_Amazon_Instant_Video.json', help='Path to JSON reviews file')
    parser.add_argument('--json_meta', default='meta_Amazon_Instant_Video.json', help='Path to meta Amazon Instant Video file')
    parser.add_argument('--output', default='combined_amazon_reviews.json', help='Output file path')
    parser.add_argument('--format', default='json', choices=['csv', 'json', 'excel'], help='Output file format')
    parser.add_argument('--samples', type=int, default=10000, help='Number of samples to process (0 for all)')
    args = parser.parse_args()

    max_samples = args.samples // 3 if args.samples > 0 else None

    print(f"Parsing {args.txt} file...")
    txt_reviews = parse_amazon_meta_txt(args.txt, max_samples)
    print(f"Extracted {len(txt_reviews)} reviews from text file")

    print(f"Parsing {args.json_reviews} file...")
    json_reviews = parse_json_reviews(args.json_reviews, max_samples)
    print(f"Extracted {len(json_reviews)} reviews from review JSON")

    print(f"Parsing {args.json_meta} file...")
    meta_reviews = parse_meta_instant_video_json(args.json_meta, max_samples)
    print(f"Extracted {len(meta_reviews)} items from meta JSON")

    print("Combining datasets and processing...")
    combined_df = combine_review_data(txt_reviews, json_reviews, meta_reviews, max_total_samples=args.samples)
    print(f"Combined dataset has {len(combined_df)} unique reviews")

    print(f"Saving to {args.output}...")
    save_combined_data(combined_df, args.output, format=args.format)
    print("Done!")

if __name__ == "__main__":
    main()
