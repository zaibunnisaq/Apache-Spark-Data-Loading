# Amazon Reviews Analysis - Data Storytelling with Tableau

This project combines multiple Amazon review datasets to create a comprehensive, interactive data visualization dashboard in Tableau that provides valuable business insights through data storytelling. The focus is on analyzing customer sentiment, review patterns, and product performance in a visually compelling way.

## Project Overview

This project combines data from multiple Amazon review sources to create a unified dataset that enables deep analysis of customer sentiment, product trends, and review patterns. The resulting Tableau dashboards provide interactive visualizations that tell a compelling data story without requiring additional reports.

## Dataset Processing

### Data Sources
1. `amazon-meta.txt` - Structured text file containing detailed product metadata and reviews
2. `reviews_Amazon_Instant_Video.json` - JSON file with Amazon Instant Video reviews 
3. `meta_Amazon_Instant_Video.json` - JSON file with Amazon Instant Video metadata

### Data Processing Script

The Python script `amazon_reviews_processor.py` performs the following operations:

1. **Parsing Multiple Data Sources**:
   - Extracts review data from the structured Amazon meta text file
   - Processes JSON review data
   - Integrates metadata from the meta JSON file

2. **Data Cleaning & Standardization**:
   - Normalizes timestamps to consistent format with proper date conversion
   - Standardizes categories (e.g., "Books" → "Books & Literature")
   - Handles empty fields and standardizes formats

3. **Deduplication & Sample Management**:
   - Creates unique review identifiers to remove duplicates
   - Allows processing of sample subsets for testing and development

The script includes three main parsing functions:

```python
# Parse text file with product metadata and reviews
parse_amazon_meta_txt(file_path, max_samples=None)

# Parse JSON review file
parse_json_reviews(file_path, max_samples=None)

# Parse JSON metadata file
parse_meta_instant_video_json(file_path, max_samples=None)
```

The data combination function merges all datasets and handles deduplication:

```python
combine_review_data(*datasets, max_total_samples=None)
```

#### Script Execution

The script can be run with various parameters:

```bash
python amazon_reviews_processor.py --samples 10000 --format csv
```

Parameters include:
- `--txt`: Path to amazon-meta.txt file
- `--json_reviews`: Path to JSON reviews file
- `--json_meta`: Path to meta JSON file  
- `--output`: Output file path
- `--format`: Output format (csv, json, excel)
- `--samples`: Number of samples to process (0 for all)

## Tableau Dashboard

The interactive Tableau dashboard consists of multiple views that offer different perspectives on the Amazon review data:

### 1. Average Rating of Products
![Average Rating Dashboard]

This dashboard displays the distribution of product ratings, allowing users to identify top-performing products and those needing improvement. It includes:
- Average rating by product category
- Rating trends over time
- Rating distribution visualization

### 2. Word Cloud
![Word Cloud Dashboard]

The word cloud visualization highlights frequently occurring terms in customer reviews, helping to identify:
- Common praise points in positive reviews
- Frequent complaints in negative reviews
- Topic clusters that emerge from review text

### 3. Sentiment of Reviews
![Sentiment Dashboard]

This dashboard analyzes the emotional tone of reviews using natural language processing:
- Sentiment distribution across product categories
- Sentiment trends over time
- Correlation between sentiment and rating

### 4. Helpfulness of Reviews
![Helpfulness Dashboard]

This visualization focuses on which reviews customers find most helpful:
- Relationship between review length and helpfulness
- Verified purchase impact on helpfulness rating
- Most helpful positive and negative reviews

### 5. Year Level Dashboard
![Year Level Dashboard]

This time-based dashboard shows review patterns across different years:
- Seasonal trends in review volume
- Year-over-year comparison of ratings
- Holiday season review patterns

### 6. Product Level Dashboard
![Product Dashboard]

This detailed view provides product-specific insights:
- Individual product performance metrics
- Comparison between similar products
- Review volume vs. rating correlation

## Dashboard Interactivity

The Tableau dashboards offer rich interactive features:
- **Filters**: Filter by date range, product category, star rating
- **Drill-down capabilities**: Navigate from category-level to product-level insights
- **Tooltips**: Reveal additional data points on hover
- **Highlighting**: Cross-highlight related data across multiple visualizations
- **Parameters**: Adjust thresholds for sentiment analysis and other calculations

## Conclusion

This project demonstrates how combining multiple Amazon review datasets and creating interactive visualizations can provide valuable business insights. The Tableau dashboards enable data-driven decision making by highlighting patterns in customer sentiment, product performance, and review characteristics.
