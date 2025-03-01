import os
import time
import logging
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
from wordcloud import WordCloud
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import plotly.io as pio
import gzip
import json
import re
from collections import Counter

class AmazonReviewsEDA:
    def __init__(self, input_path, log_path="E:/dataviz/logs", output_path="E:/dataviz/eda_output", viz_path="E:/dataviz/visualizations"):
        self.input_path = input_path
        self.log_path = log_path.replace("\\", "/")
        self.output_path = output_path.replace("\\", "/")
        self.viz_path = viz_path.replace("\\", "/")
        self.df = None
        self.analyzer = SentimentIntensityAnalyzer()
        self.sample_size = 500  # Adjust default sample size if needed
        
        # Create necessary directories
        for path in [log_path, output_path, viz_path]:
            os.makedirs(path, exist_ok=True)
            
        self.log_file = os.path.join(
            log_path, f"eda_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        
        # Configure logging
        logging.basicConfig(
            filename=self.log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def log_message(self, message):
        print(message)
        logging.info(message)

    def load_data_sample(self):
        self.log_message(" Loading a small data sample for EDA using Python gzip and native JSON parsing...")
        try:
            # Verify file existence
            if os.path.exists(self.input_path):
                file_size = os.path.getsize(self.input_path)
                self.log_message(f"File found! Size: {file_size} bytes")
            else:
                self.log_message(f" ERROR: File {self.input_path} not found!")
                raise FileNotFoundError(f"File {self.input_path} not found!")
            
            # Use Python's gzip and json to read only a small number of lines
            sample_line_count = 100  # You can adjust this as needed
            parsed_records = []
            with gzip.open(self.input_path, 'rt', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    if i >= sample_line_count:
                        break
                    try:
                        record = json.loads(line)
                        parsed_records.append(record)
                    except json.JSONDecodeError:
                        self.log_message(f"Skipping malformed JSON line at index {i}.")
            
            self.log_message(f"Parsed {len(parsed_records)} valid JSON records from the gzip file.")
            
            if not parsed_records:
                self.log_message(" No valid JSON records were parsed. Exiting data load.")
                return
            
            # Create a pandas DataFrame
            self.df = pd.DataFrame(parsed_records)
            
            # Keep only the columns we need
            target_columns = ["reviewText", "summary", "asin", "overall", "reviewTime", "verified", "reviewerID", "category", "brand"]
            existing_columns = self.df.columns
            valid_columns = [c for c in target_columns if c in existing_columns]
            self.log_message(f"Found columns: {valid_columns}")
            
            # Keep only the needed columns
            self.df = self.df[valid_columns]
            
            # Limit to top 20 rows
            self.df = self.df.head(20)
            
            self.log_message(f"DataFrame shape: {self.df.shape}")
            self.log_message(" Data successfully loaded for EDA.")
            
        except Exception as e:
            self.log_message(f" Error loading data: {str(e)}")
            import traceback
            self.log_message(f"Traceback: {traceback.format_exc()}")
            raise

    def data_understanding(self):
        self.log_message(" Performing data understanding and summary statistics...")
        row_count, col_count = self.df.shape
        self.log_message(f"Dataset shape: {row_count} rows x {col_count} columns")
        
        self.log_message("Column types:")
        for column, dtype in self.df.dtypes.items():
            self.log_message(f"  - {column}: {dtype}")
        
        # Missing values analysis
        missing_counts = self.df.isna().sum()
        missing_percent = (missing_counts / row_count) * 100
        missing_df = pd.DataFrame({
            'Column': missing_counts.index,
            'Missing Count': missing_counts.values,
            'Missing Percent': missing_percent.values
        })
        missing_df.to_csv(f"{self.output_path}/missing_values.csv", index=False)
        self.log_message(f"Missing values analysis saved to {self.output_path}/missing_values.csv")
        
        # Numeric statistics
        numeric_cols = self.df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        if numeric_cols:
            stats_df = self.df[numeric_cols].describe()
            stats_df.to_csv(f"{self.output_path}/numeric_stats.csv")
            self.log_message(f"Numeric statistics saved to {self.output_path}/numeric_stats.csv")
        
        # Ratings distribution if available
        if 'overall' in self.df.columns:
            ratings_dist = self.df['overall'].value_counts().reset_index()
            ratings_dist.columns = ['overall', 'count']
            fig = px.bar(
                ratings_dist, 
                x="overall", 
                y="count", 
                title="Distribution of Review Ratings",
                labels={"overall": "Rating", "count": "Number of Reviews"},
                color="overall",
                color_continuous_scale="RdBu"
            )
            pio.write_html(fig, f"{self.viz_path}/rating_distribution.html")
            self.log_message(f"Rating distribution visualization saved to {self.viz_path}/rating_distribution.html")
        
        self.log_message(" Data understanding and summary statistics completed")

    def query_based_eda(self):
        self.log_message("Performing query-based EDA...")
        
        # Query 1: Top products by review count
        if 'asin' in self.df.columns:
            self.log_message("Query 1: Finding most reviewed products...")
            top_products = self.df['asin'].value_counts().reset_index().head(5)
            top_products.columns = ['asin', 'count']
            top_products.to_csv(f"{self.output_path}/top_reviewed_products.csv", index=False)
            
            fig = px.bar(
                top_products, 
                x="asin", 
                y="count", 
                title="Most Reviewed Products",
                labels={"asin": "Product ID", "count": "Number of Reviews"},
                color="count",
                color_continuous_scale="Viridis"
            )
            pio.write_html(fig, f"{self.viz_path}/top_products.html")
            self.log_message("Most reviewed products saved and visualized")
        
        # Query 3: Review length vs rating
        if all(col in self.df.columns for col in ["reviewText", "overall"]):
            self.log_message("Query 3: Analyzing correlation between review length and rating...")
            self.df['review_length'] = self.df['reviewText'].apply(lambda x: len(str(x)) if pd.notna(x) else 0)
            
            length_by_rating = self.df.groupby('overall')['review_length'].agg(['mean', 'count']).reset_index()
            length_by_rating.columns = ['overall', 'avg_length', 'count']
            length_by_rating.to_csv(f"{self.output_path}/review_length_by_rating.csv", index=False)
            
            fig = px.bar(
                length_by_rating, 
                x="overall", 
                y="avg_length", 
                title="Average Review Length by Rating",
                labels={"overall": "Rating", "avg_length": "Average Review Length (characters)"},
                color="count",
                color_continuous_scale="Viridis"
            )
            pio.write_html(fig, f"{self.viz_path}/review_length_by_rating.html")
            
            fig_scatter = px.scatter(
                self.df.head(100),
                x="overall",
                y="review_length",
                title="Review Length vs Rating (Sample)",
                labels={"overall": "Rating", "review_length": "Review Length (characters)"},
                color="overall",
                color_continuous_scale="RdBu"
            )
            pio.write_html(fig_scatter, f"{self.viz_path}/review_length_scatter.html")
            self.log_message("Review length analysis saved and visualized")
        
        # Query 4: Verified vs non-verified purchases
        if all(col in self.df.columns for col in ["verified", "overall"]):
            self.log_message("Query 4: Comparing verified vs non-verified purchase ratings...")
            verified_ratings = self.df.groupby('verified')['overall'].agg(['mean', 'count']).reset_index()
            verified_ratings.columns = ['verified', 'avg_rating', 'count']
            verified_ratings.to_csv(f"{self.output_path}/verified_vs_nonverified.csv", index=False)
            
            fig = px.bar(
                verified_ratings, 
                x="verified", 
                y="avg_rating", 
                title="Average Rating: Verified vs Non-Verified Purchases",
                labels={"verified": "Verified Purchase", "avg_rating": "Average Rating"},
                color="count",
                color_continuous_scale="Viridis"
            )
            pio.write_html(fig, f"{self.viz_path}/verified_vs_nonverified.html")
            self.log_message("Verified vs non-verified purchase analysis saved and visualized")
        
        # Query 5: Negative keywords analysis
        if "reviewText" in self.df.columns:
            self.log_message("Query 5: Analyzing negative keywords in reviews...")
            negative_words = ['refund', 'return', 'defective', 'broken', 'disappointed', 'waste', 'poor', 'bad']
            
            # Create a function to check for negative words
            def contains_negative(text):
                if pd.isna(text):
                    return 0
                text = str(text).lower()
                return 1 if any(word in text for word in negative_words) else 0
            
            self.df['contains_negative'] = self.df['reviewText'].apply(contains_negative)
            
            negative_counts = pd.DataFrame({
                'negative_reviews': [self.df['contains_negative'].sum()],
                'total_reviews': [len(self.df)]
            })
            negative_counts['percentage'] = (negative_counts['negative_reviews'] / negative_counts['total_reviews']) * 100
            negative_counts.to_csv(f"{self.output_path}/negative_keywords.csv", index=False)
            
            labels = ['Contains Negative Keywords', 'No Negative Keywords']
            values = [
                negative_counts['negative_reviews'].iloc[0], 
                negative_counts['total_reviews'].iloc[0] - negative_counts['negative_reviews'].iloc[0]
            ]
            fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3, marker_colors=['#FF6B6B', '#4ECDC4'])])
            fig.update_layout(title_text="Reviews Containing Negative Keywords")
            pio.write_html(fig, f"{self.viz_path}/negative_keywords_pie.html")
            
            # Create word cloud for negative reviews
            negative_reviews = self.df[self.df['contains_negative'] == 1]['reviewText'].dropna()
            if len(negative_reviews) > 0:
                neg_texts = " ".join(negative_reviews.astype(str).tolist())
                if len(neg_texts) > 0:
                    neg_wordcloud = WordCloud(width=800, height=400, background_color='white', max_words=100, colormap='Reds').generate(neg_texts)
                    plt.figure(figsize=(10, 5))
                    plt.imshow(neg_wordcloud, interpolation='bilinear')
                    plt.axis("off")
                    plt.title("Common Words in Negative Reviews")
                    plt.savefig(f"{self.viz_path}/negative_wordcloud.png")
                    plt.close()
                    self.log_message("Negative reviews word cloud saved")
            
            self.log_message("Negative keywords analysis saved and visualized")
            
        # ADDED QUERY 1: Time-series analysis of reviews
        if "reviewTime" in self.df.columns:
            self.log_message("ADDED Query 1: Analyzing review trends over time...")
            
            # Convert review time to datetime
            try:
                self.df['review_date'] = pd.to_datetime(self.df['reviewTime'], errors='coerce')
                
                # Extract month and year for trend analysis
                self.df['review_month'] = self.df['review_date'].dt.to_period('M')
                
                # Monthly review count
                monthly_counts = self.df.groupby('review_month').size().reset_index(name='review_count')
                monthly_counts['review_month'] = monthly_counts['review_month'].astype(str)
                monthly_counts.to_csv(f"{self.output_path}/monthly_review_trends.csv", index=False)
                
                # Monthly average rating
                monthly_ratings = self.df.groupby('review_month')['overall'].mean().reset_index()
                monthly_ratings['review_month'] = monthly_ratings['review_month'].astype(str)
                monthly_ratings.to_csv(f"{self.output_path}/monthly_rating_trends.csv", index=False)
                
                # Create time series visualizations
                fig_count = px.line(
                    monthly_counts, 
                    x="review_month", 
                    y="review_count",
                    title="Monthly Review Volume Over Time",
                    labels={"review_month": "Month", "review_count": "Number of Reviews"},
                    markers=True
                )
                pio.write_html(fig_count, f"{self.viz_path}/monthly_review_volume.html")
                
                fig_rating = px.line(
                    monthly_ratings, 
                    x="review_month", 
                    y="overall",
                    title="Monthly Average Rating Over Time",
                    labels={"review_month": "Month", "overall": "Average Rating"},
                    markers=True
                )
                fig_rating.update_layout(yaxis_range=[1, 5])
                pio.write_html(fig_rating, f"{self.viz_path}/monthly_rating_trends.html")
                
                # Combined visualization
                fig_combined = go.Figure()
                fig_combined.add_trace(go.Scatter(
                    x=monthly_counts['review_month'],
                    y=monthly_counts['review_count'],
                    name='Review Count',
                    mode='lines+markers',
                    yaxis='y'
                ))
                fig_combined.add_trace(go.Scatter(
                    x=monthly_ratings['review_month'],
                    y=monthly_ratings['overall'],
                    name='Average Rating',
                    mode='lines+markers',
                    yaxis='y2'
                ))
                fig_combined.update_layout(
                    title='Review Volume and Rating Trends Over Time',
                    xaxis=dict(title='Month'),
                    yaxis=dict(title='Number of Reviews', side='left'),
                    yaxis2=dict(title='Average Rating', side='right', overlaying='y', range=[1, 5]),
                    legend=dict(orientation='h', y=1.1)
                )
                pio.write_html(fig_combined, f"{self.viz_path}/combined_time_trends.html")
                
                self.log_message("Review time trends saved and visualized")
            except Exception as e:
                self.log_message(f"Error in time-series analysis: {str(e)}")
        
        # ADDED QUERY 2: Products with most polarized reviews
        if all(col in self.df.columns for col in ["asin", "overall"]):
            self.log_message("ADDED Query 2: Finding products with the most polarized reviews...")
            
            # Calculate polarization metrics for each product
            # Products with high counts of both 1-star and 5-star reviews
            
            # First, create a pivot table of ratings
            product_ratings = pd.crosstab(
                index=self.df['asin'],
                columns=self.df['overall'],
                normalize='index'
            ).reset_index()
            
            # If needed columns exist (1-star and 5-star)
            if 1.0 in product_ratings.columns and 5.0 in product_ratings.columns:
                # Calculate polarization score: high values of both 1-star and 5-star reviews
                product_ratings['polarization_score'] = product_ratings[1.0] * product_ratings[5.0] * 100
                
                # Get product review counts for context
                product_counts = self.df['asin'].value_counts().reset_index()
                product_counts.columns = ['asin', 'review_count']
                
                # Merge with polarization scores
                polarized_products = pd.merge(product_ratings, product_counts, on='asin')
                
                # Filter for products with at least a minimum number of reviews
                min_reviews = 2  # Adjust based on your data
                polarized_products = polarized_products[polarized_products['review_count'] >= min_reviews]
                
                # Sort by polarization score
                top_polarized = polarized_products.sort_values('polarization_score', ascending=False).head(10)
                top_polarized.to_csv(f"{self.output_path}/polarized_products.csv", index=False)
                
                # Create visualizations
                fig_polar = px.bar(
                    top_polarized.head(5),
                    x='asin',
                    y='polarization_score',
                    title='Top 5 Products with Most Polarized Reviews',
                    labels={'asin': 'Product ID', 'polarization_score': 'Polarization Score'},
                    color='review_count',
                    color_continuous_scale='Viridis'
                )
                pio.write_html(fig_polar, f"{self.viz_path}/polarized_products.html")
                
                # Distribution of ratings for top polarized products
                top_product_ids = top_polarized.head(3)['asin'].tolist()
                if top_product_ids:
                    top_product_reviews = self.df[self.df['asin'].isin(top_product_ids)]
                    
                    fig_dist = px.histogram(
                        top_product_reviews,
                        x='overall',
                        color='asin',
                        barmode='group',
                        nbins=5,
                        title='Rating Distribution for Most Polarized Products',
                        labels={'overall': 'Rating', 'count': 'Number of Reviews'},
                        category_orders={'overall': [1.0, 2.0, 3.0, 4.0, 5.0]}
                    )
                    pio.write_html(fig_dist, f"{self.viz_path}/polarized_rating_distribution.html")
                
                self.log_message("Polarized products analysis saved and visualized")
            else:
                self.log_message("Insufficient rating data for polarization analysis")
        
        # ADDED QUERY 3: Analysis of potentially fake-looking reviews
        if "reviewText" in self.df.columns:
            self.log_message("ADDED Query 3: Analyzing potentially fake-looking reviews...")
            
            # Define metrics for potentially fake-looking reviews
            
            # 1. Repetition of words (unusual repetition patterns)
            def word_repetition_score(text):
                if pd.isna(text) or len(str(text).strip()) == 0:
                    return 0
                    
                words = re.findall(r'\b\w+\b', str(text).lower())
                if len(words) <= 1:
                    return 0
                    
                # Count word frequencies
                word_counts = Counter(words)
                
                # Calculate repetition metrics
                unique_words = len(word_counts)
                total_words = len(words)
                
                if total_words == 0:
                    return 0
                
                # Repetition score: lower ratio of unique words indicates more repetition
                repetition_score = 1 - (unique_words / total_words)
                
                # Check for excessive use of most common word
                if unique_words > 0:
                    most_common_word, most_common_count = word_counts.most_common(1)[0]
                    most_common_ratio = most_common_count / total_words
                    
                    # Boost score if single word represents large portion of text
                    if most_common_ratio > 0.25 and total_words > 5:
                        repetition_score += most_common_ratio
                
                return min(repetition_score, 1.0)  # Cap at 1.0
            
            # 2. Unusual patterns like all caps, excessive punctuation, etc.
            def unusual_patterns_score(text):
                if pd.isna(text) or len(str(text).strip()) == 0:
                    return 0
                
                text = str(text)
                total_chars = len(text)
                if total_chars == 0:
                    return 0
                
                # Check for ALL CAPS
                caps_ratio = sum(1 for c in text if c.isupper()) / total_chars
                
                # Check for excessive punctuation
                punctuation = sum(1 for c in text if c in '!?.,:;')
                punct_ratio = punctuation / total_chars
                
                # Check for repeated punctuation (!!!, ???, etc.)
                repeated_punct = len(re.findall(r'([!?.]{2,})', text))
                
                # Combined score
                pattern_score = caps_ratio * 0.5 + punct_ratio * 0.3 + (repeated_punct / 5) * 0.2
                
                return min(pattern_score, 1.0)  # Cap at 1.0
            
            # Calculate fake-looking scores
            self.df['repetition_score'] = self.df['reviewText'].apply(word_repetition_score)
            self.df['unusual_patterns_score'] = self.df['reviewText'].apply(unusual_patterns_score)
            self.df['fake_looking_score'] = (self.df['repetition_score'] * 0.7 + self.df['unusual_patterns_score'] * 0.3)
            
            # Find reviews with high fake-looking scores
            suspicious_threshold = 0.5  # Adjust based on your data
            suspicious_reviews = self.df[self.df['fake_looking_score'] >= suspicious_threshold].copy()
            suspicious_reviews = suspicious_reviews.sort_values('fake_looking_score', ascending=False)
            
            # Save results
            if len(suspicious_reviews) > 0:
                suspicious_reviews.to_csv(f"{self.output_path}/suspicious_reviews.csv", index=False)
                
                # Analyze by product
                product_suspicion = self.df.groupby('asin')['fake_looking_score'].agg(['mean', 'count']).reset_index()
                product_suspicion.columns = ['asin', 'avg_fake_score', 'review_count']
                
                # Filter for products with minimum reviews
                min_reviews = 2  # Adjust based on your data
                product_suspicion = product_suspicion[product_suspicion['review_count'] >= min_reviews]
                
                # Sort by average fake score
                suspicious_products = product_suspicion.sort_values('avg_fake_score', ascending=False).head(10)
                suspicious_products.to_csv(f"{self.output_path}/suspicious_products.csv", index=False)
                
                # Visualizations
                fig_fake = px.bar(
                    suspicious_products.head(5),
                    x='asin',
                    y='avg_fake_score',
                    title='Products with Highest Average Suspicious Review Scores',
                    labels={'asin': 'Product ID', 'avg_fake_score': 'Avg. Suspicious Score'},
                    color='review_count',
                    color_continuous_scale='Reds'
                )
                pio.write_html(fig_fake, f"{self.viz_path}/suspicious_products.html")
                
                # Distribution of fake scores
                fig_dist = px.histogram(
                    self.df,
                    x='fake_looking_score',
                    title='Distribution of Suspicious Review Scores',
                    labels={'fake_looking_score': 'Suspicious Score'},
                    color_discrete_sequence=['coral']
                )
                fig_dist.add_vline(x=suspicious_threshold, line_dash="dash", line_color="red", annotation_text="Suspicious Threshold")
                pio.write_html(fig_dist, f"{self.viz_path}/suspicious_score_distribution.html")
                
                # If we have category data as well
                if 'category' in self.df.columns:
                    category_suspicion = self.df.groupby('category')['fake_looking_score'].mean().reset_index()
                    category_suspicion = category_suspicion.sort_values('fake_looking_score', ascending=False)
                    
                    fig_cat = px.bar(
                        category_suspicion.head(5),
                        x='category',
                        y='fake_looking_score',
                        title='Categories with Highest Average Suspicious Review Scores',
                        labels={'category': 'Product Category', 'fake_looking_score': 'Avg. Suspicious Score'},
                        color='fake_looking_score',
                        color_continuous_scale='Reds'
                    )
                    pio.write_html(fig_cat, f"{self.viz_path}/suspicious_categories.html")
                
                self.log_message("Fake-looking reviews analysis saved and visualized")
            else:
                self.log_message("No suspicious reviews found with the current threshold")
        
        self.log_message("Query-based EDA completed")

    def text_analysis(self):
        self.log_message("Performing text analysis...")
        if "reviewText" in self.df.columns:
            self.log_message("Generating word cloud...")
            
            # Basic text preprocessing
            def preprocess_text(text):
                if pd.isna(text):
                    return []
                text = str(text).lower()
                # Remove punctuation and split into words
                words = re.findall(r'\b\w+\b', text)
                # Remove stopwords
                stopwords = {'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours', 
                            'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself', 
                            'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 
                            'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 
                            'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 
                            'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 
                            'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before', 
                            'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 
                            'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 
                            'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 
                            'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 
                            'just', 'don', 'should', 'now'}
                words = [word for word in words if word not in stopwords and len(word) > 2]
                return words
            
            # Process all reviews and create word cloud
            all_words = []
            for text in self.df['reviewText'].dropna():
                all_words.extend(preprocess_text(text))
            
            if all_words:
                text = " ".join(all_words)
                wordcloud = WordCloud(width=800, height=400, background_color='white', max_words=100, colormap='viridis').generate(text)
                plt.figure(figsize=(10, 5))
                plt.imshow(wordcloud, interpolation='bilinear')
                plt.axis("off")
                plt.title("Common Words in Reviews")
                plt.savefig(f"{self.viz_path}/wordcloud.png")
                plt.close()
                self.log_message(f"Word cloud saved to {self.viz_path}/wordcloud.png")
            
            # Simple sentiment analysis based on keywords
            self.log_message("Performing sentiment analysis...")
            pos_keywords = ['good', 'great', 'excellent', 'love', 'perfect', 'best', 'amazing', 'awesome', 
                           'happy', 'pleased', 'satisfied', 'recommend', 'quality', 'fantastic', 'wonderful', 'superb']
            neg_keywords = ['bad', 'poor', 'terrible', 'hate', 'disappointing', 'worst', 'awful', 'refund',
                           'broken', 'defective', 'issue', 'problem', 'complaint', 'fail', 'waste', 'regret', 'unhappy']
            
            def get_sentiment(text):
                if pd.isna(text):
                    return "Neutral"
                text = str(text).lower()
                
                # Check for positive and negative keywords
                pos_count = sum(1 for word in pos_keywords if word in text)
                neg_count = sum(1 for word in neg_keywords if word in text)
                
                # Use VADER for more
                # Use VADER for more accurate sentiment analysis
                vader_scores = self.analyzer.polarity_scores(text)
                compound_score = vader_scores['compound']
                
                if compound_score >= 0.05:
                    return "Positive"
                elif compound_score <= -0.05:
                    return "Negative"
                else:
                    return "Neutral"
            
            self.df['sentiment'] = self.df['reviewText'].apply(get_sentiment)
            
            sentiment_counts = self.df['sentiment'].value_counts().reset_index()
            sentiment_counts.columns = ['sentiment', 'count']
            sentiment_counts.to_csv(f"{self.output_path}/sentiment_counts.csv", index=False)
            
            colors = {'Positive': '#4CAF50', 'Neutral': '#FFC107', 'Negative': '#F44336'}
            fig = px.pie(
                sentiment_counts, 
                values='count', 
                names='sentiment', 
                title='Sentiment Distribution',
                color='sentiment',
                color_discrete_map=colors
            )
            pio.write_html(fig, f"{self.viz_path}/sentiment_distribution.html")
            
            # Sentiment by rating
            sentiment_by_rating = self.df.groupby(['overall', 'sentiment']).size().reset_index(name='count')
            fig_sentiment_rating = px.bar(
                sentiment_by_rating,
                x="overall",
                y="count",
                color="sentiment",
                title="Sentiment Distribution by Rating",
                labels={"overall": "Rating", "count": "Number of Reviews", "sentiment": "Sentiment"},
                color_discrete_map=colors
            )
            pio.write_html(fig_sentiment_rating, f"{self.viz_path}/sentiment_by_rating.html")
            
            # Additional analysis: VADER sentiment scores distribution
            self.df['vader_compound'] = self.df['reviewText'].apply(
                lambda x: self.analyzer.polarity_scores(str(x))['compound'] if pd.notna(x) else None
            )
            
            fig_vader = px.histogram(
                self.df.dropna(subset=['vader_compound']),
                x="vader_compound",
                title="Distribution of VADER Sentiment Scores",
                labels={"vader_compound": "Sentiment Score (Compound)"},
                color_discrete_sequence=['teal'],
                nbins=20
            )
            fig_vader.add_vline(x=0.05, line_dash="dash", line_color="green", 
                                annotation_text="Positive Threshold")
            fig_vader.add_vline(x=-0.05, line_dash="dash", line_color="red", 
                                annotation_text="Negative Threshold")
            pio.write_html(fig_vader, f"{self.viz_path}/vader_sentiment_distribution.html")
            
            self.log_message("Sentiment analysis saved and visualized")
            
            # Enhanced text analysis for category-specific phrases
            if 'category' in self.df.columns:
                self.log_message("Analyzing category-specific language patterns...")
                
                # Group by category
                categories = self.df['category'].dropna().unique()
                
                for category in categories[:5]:  # Limit to top 5 categories to avoid excessive processing
                    category_reviews = self.df[self.df['category'] == category]['reviewText'].dropna()
                    
                    if len(category_reviews) >= 3:  # Only process if we have enough reviews
                        # Extract common phrases and terms
                        category_text = " ".join(category_reviews.astype(str))
                        
                        # Generate category-specific word cloud
                        cat_wordcloud = WordCloud(width=800, height=400, 
                                                  background_color='white', 
                                                  max_words=50, 
                                                  colormap='plasma').generate(category_text)
                        plt.figure(figsize=(8, 4))
                        plt.imshow(cat_wordcloud, interpolation='bilinear')
                        plt.axis("off")
                        plt.title(f"Common Words in {category} Reviews")
                        plt.savefig(f"{self.viz_path}/wordcloud_{category.replace(' ', '_').replace('/', '_')[:30]}.png")
                        plt.close()
                
                self.log_message("Category-specific text analysis completed")
        
        self.log_message("Text analysis completed")

    def correlation_and_insights(self):
        self.log_message("Analyzing correlations and business insights...")
        
        if len(self.df) < 2:
            self.log_message("Not enough data to compute correlation. Skipping correlation matrix.")
            return
        
        # Add review length column if not already there
        if 'review_length' not in self.df.columns and 'reviewText' in self.df.columns:
            self.df['review_length'] = self.df['reviewText'].apply(lambda x: len(str(x)) if pd.notna(x) else 0)
        
        # Compute correlation matrix for numeric columns
        numeric_cols = self.df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        if len(numeric_cols) >= 2:
            corr_matrix = self.df[numeric_cols].corr()
            corr_matrix.to_csv(f"{self.output_path}/correlation_matrix.csv")
            
            plt.figure(figsize=(10, 8))
            sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1, fmt=".2f")
            plt.title('Correlation Matrix')
            plt.tight_layout()
            plt.savefig(f"{self.viz_path}/correlation_heatmap.png")
            plt.close()
            self.log_message("Correlation heatmap saved")
            
            # Enhanced correlation analysis with scatter plots for key relationships
            if all(col in numeric_cols for col in ['overall', 'review_length']):
                fig_scatter = px.scatter(
                    self.df,
                    x='review_length',
                    y='overall',
                    title='Rating vs Review Length',
                    labels={'review_length': 'Review Length (characters)', 'overall': 'Rating'},
                    trendline='ols',
                    color='overall',
                    color_continuous_scale='RdBu'
                )
                pio.write_html(fig_scatter, f"{self.viz_path}/rating_vs_length_scatter.html")
            
            # Check if we have sentiment scores to correlate
            if 'vader_compound' in numeric_cols:
                fig_sent_corr = px.scatter(
                    self.df.dropna(subset=['vader_compound']),
                    x='vader_compound',
                    y='overall',
                    title='Rating vs Sentiment Score',
                    labels={'vader_compound': 'Sentiment Score', 'overall': 'Rating'},
                    trendline='ols',
                    color='overall',
                    color_continuous_scale='RdBu'
                )
                pio.write_html(fig_sent_corr, f"{self.viz_path}/rating_vs_sentiment_scatter.html")
        
        # Generate business insights
        if 'asin' in self.df.columns and 'overall' in self.df.columns:
            self.log_message("Generating business insights...")
            
            product_insights = self.df.groupby('asin').agg({
                'overall': ['count', 'mean', 'std'],
                'review_length': ['mean'] if 'review_length' in self.df.columns else []
            }).reset_index()
            
            # Flatten the column hierarchy
            product_insights.columns = [
                '_'.join(col).strip('_') for col in product_insights.columns.values
            ]
            
            # Calculate additional metrics
            min_reviews = 2  # Minimum reviews to consider a product
            popular_products = product_insights[product_insights['overall_count'] >= min_reviews]
            
            if len(popular_products) > 0:
                # Top rated products
                top_rated = popular_products.sort_values(['overall_mean', 'overall_count'], ascending=[False, False]).head(10)
                top_rated.to_csv(f"{self.output_path}/top_rated_products.csv", index=False)
                
                # Products with most reviews
                most_reviewed = popular_products.sort_values('overall_count', ascending=False).head(10)
                most_reviewed.to_csv(f"{self.output_path}/most_reviewed_products.csv", index=False)
                
                # Products with most variation in ratings
                if 'overall_std' in popular_products.columns:
                    most_variable = popular_products.sort_values(['overall_std', 'overall_count'], ascending=[False, False]).head(10)
                    most_variable.to_csv(f"{self.output_path}/most_variable_products.csv", index=False)
                
                # Visualize product landscape
                fig = px.scatter(
                    popular_products, 
                    x="overall_count", 
                    y="overall_mean", 
                    title="Product Rating vs Popularity",
                    labels={"overall_count": "Number of Reviews", "overall_mean": "Average Rating"},
                    hover_data=["asin"],
                    color="overall_mean",
                    size="overall_count",
                    color_continuous_scale="RdYlGn"
                )
                pio.write_html(fig, f"{self.viz_path}/rating_vs_popularity.html")
                
                # Overall statistics gauge chart
                overall_avg = self.df['overall'].mean()
                
                fig_gauge = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = overall_avg,
                    title = {'text': "Average Product Rating"},
                    gauge = {
                        'axis': {'range': [1, 5]},
                        'bar': {'color': "royalblue"},
                        'steps': [
                            {'range': [1, 2], 'color': "#FF4136"},
                            {'range': [2, 3], 'color': "#FFDC00"},
                            {'range': [3, 4], 'color': "#2ECC40"},
                            {'range': [4, 5], 'color': "#0074D9"}
                        ],
                    }
                ))
                pio.write_html(fig_gauge, f"{self.viz_path}/overall_rating_gauge.html")
                
                # Top rated products bar chart
                fig_top = px.bar(
                    top_rated.head(5),
                    x="asin",
                    y="overall_mean",
                    title="Top 5 Highest Rated Products",
                    labels={"asin": "Product ID", "overall_mean": "Average Rating"},
                    color="overall_mean",
                    color_continuous_scale="RdYlGn",
                    text="overall_count"
                )
                fig_top.update_traces(texttemplate='%{text} reviews', textposition='outside')
                pio.write_html(fig_top, f"{self.viz_path}/top_rated_products.html")
                
                # Brand analysis if the data is available
                if 'brand' in self.df.columns:
                    brand_performance = self.df.groupby('brand').agg({
                        'overall': ['count', 'mean'],
                        'asin': 'nunique'  # Count unique products per brand
                    }).reset_index()
                    
                    brand_performance.columns = ['brand', 'review_count', 'avg_rating', 'product_count']
                    brand_performance = brand_performance[brand_performance['review_count'] >= min_reviews]
                    
                    # Top performing brands
                    top_brands = brand_performance.sort_values(['avg_rating', 'review_count'], ascending=[False, False]).head(10)
                    top_brands.to_csv(f"{self.output_path}/top_brands.csv", index=False)
                    
                    # Brand visualization
                    fig_brands = px.scatter(
                        brand_performance,
                        x="product_count",
                        y="avg_rating",
                        size="review_count",
                        title="Brand Performance Overview",
                        labels={
                            "product_count": "Number of Products", 
                            "avg_rating": "Average Rating",
                            "review_count": "Number of Reviews"
                        },
                        hover_data=["brand"],
                        color="avg_rating",
                        color_continuous_scale="RdYlGn"
                    )
                    pio.write_html(fig_brands, f"{self.viz_path}/brand_performance.html")
                    
                    # Top brands bar chart
                    fig_top_brands = px.bar(
                        top_brands.head(5),
                        x="brand",
                        y="avg_rating",
                        title="Top 5 Highest Rated Brands",
                        labels={"brand": "Brand", "avg_rating": "Average Rating"},
                        color="review_count",
                        color_continuous_scale="Viridis",
                        text="product_count"
                    )
                    fig_top_brands.update_traces(texttemplate='%{text} products', textposition='outside')
                    pio.write_html(fig_top_brands, f"{self.viz_path}/top_brands.html")
        
        self.log_message("Correlation and business insights completed")

    def run_eda(self):
        try:
            self.log_message("Starting Amazon Reviews EDA")
            self.load_data_sample()
            
            if self.df is None or len(self.df) == 0:
                self.log_message("No data available for analysis. Exiting EDA process.")
                return
                
            try:
                self.data_understanding()
            except Exception as e:
                self.log_message(f"Data understanding step failed: {str(e)}")
                import traceback
                self.log_message(f"Traceback: {traceback.format_exc()}")
                
            try:
                self.query_based_eda()
            except Exception as e:
                self.log_message(f"Query-based EDA step failed: {str(e)}")
                import traceback
                self.log_message(f"Traceback: {traceback.format_exc()}")
                
            try:
                self.text_analysis()
            except Exception as e:
                self.log_message(f"Text analysis step failed: {str(e)}")
                import traceback
                self.log_message(f"Traceback: {traceback.format_exc()}")
                
            try:
                self.correlation_and_insights()
            except Exception as e:
                self.log_message(f"Correlation and insights step failed: {str(e)}")
                import traceback
                self.log_message(f"Traceback: {traceback.format_exc()}")
                
            self.log_message("EDA process completed successfully!")
        except Exception as e:
            self.log_message(f"EDA process failed: {str(e)}")
            import traceback
            self.log_message(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    eda_processor = AmazonReviewsEDA(
        input_path="E:/dataviz/All_Amazon_Review.json.gz",
        log_path="E:/dataviz/logs",
        output_path="E:/dataviz/eda_output",
        viz_path="E:/dataviz/visualizations"
    )
    eda_processor.run_eda()
