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
            target_columns = ["reviewText", "summary", "asin", "overall", "reviewTime", "verified", "reviewerID"]
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
                
                if any(word in text for word in pos_keywords):
                    return "Positive"
                elif any(word in text for word in neg_keywords):
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
            self.log_message("Sentiment analysis saved and visualized")
        
        self.log_message("Text analysis completed")

    def correlation_and_insights(self):
        self.log_message("Analyzing correlations and business insights...")
        
        if len(self.df) < 2:
            self.log_message("Not enough data to compute correlation. Skipping correlation matrix.")
            return
        
        # Add review length column if not already there
        if 'review_length' not in self.df.columns and 'reviewText' in self.df.columns:
            self.df['review_length'] = self.df['reviewText'].apply(lambda x: len(str(x)) if pd.notna(x) else 0)
        
        # Compute correlation matrix
        numeric_cols = self.df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        if len(numeric_cols) >= 2:
            corr_matrix = self.df[numeric_cols].corr()
            corr_matrix.to_csv(f"{self.output_path}/correlation_matrix.csv")
            
            plt.figure(figsize=(8, 6))
            sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1, fmt=".2f")
            plt.title('Correlation Matrix')
            plt.tight_layout()
            plt.savefig(f"{self.viz_path}/correlation_heatmap.png")
            plt.close()
            self.log_message("Correlation heatmap saved")
        
        # Generate business insights
        if 'asin' in self.df.columns and 'overall' in self.df.columns:
            self.log_message("Generating business insights...")
            
            product_insights = self.df.groupby('asin').agg({
                'overall': ['count', 'mean'],
            }).reset_index()
            product_insights.columns = ['asin', 'review_count', 'avg_rating']
            
            min_reviews = 2  # Minimum reviews to consider a product
            popular_products = product_insights[product_insights['review_count'] >= min_reviews]
            top_rated = popular_products.sort_values(['avg_rating', 'review_count'], ascending=[False, False]).head(10)
            
            top_rated.to_csv(f"{self.output_path}/top_rated_products.csv", index=False)
            
            fig = px.scatter(
                product_insights, 
                x="review_count", 
                y="avg_rating", 
                title="Product Rating vs Popularity",
                labels={"review_count": "Number of Reviews", "avg_rating": "Average Rating"},
                hover_data=["asin"],
                color="avg_rating",
                size="review_count",
                color_continuous_scale="RdYlGn"
            )
            pio.write_html(fig, f"{self.viz_path}/rating_vs_popularity.html")
            self.log_message("Product insights saved and visualized")
            
            if len(top_rated) > 0:
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
                
                fig_top = px.bar(
                    top_rated.head(5),
                    x="asin",
                    y="avg_rating",
                    title="Top 5 Highest Rated Products",
                    labels={"asin": "Product ID", "avg_rating": "Average Rating"},
                    color="avg_rating",
                    color_continuous_scale="RdYlGn",
                    text="review_count"
                )
                fig_top.update_traces(texttemplate='%{text} reviews', textposition='outside')
                pio.write_html(fig_top, f"{self.viz_path}/top_rated_products.html")
        
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