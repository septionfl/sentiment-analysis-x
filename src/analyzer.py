import nltk
import logging
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import pandas as pd

logger = logging.getLogger(__name__)

def download_vader_lexicon():
    """Download VADER lexicon if not available"""
    try:
        nltk.data.find('sentiment/vader_lexicon.zip')
    except LookupError:
        logger.info("Downloading VADER lexicon...")
        nltk.download('vader_lexicon')

class SentimentAnalyzer:
    def __init__(self):
        download_vader_lexicon()
        self.analyzer = SentimentIntensityAnalyzer()
        logger.info("✓ Sentiment analyzer initialized")
    
    def analyze_sentiment(self, df):
        """Perform sentiment analysis on the text"""
        logger.info("Analyzing sentiment...")
        
        df['compound'] = df['stemmed_text'].apply(lambda text: self.analyzer.polarity_scores(text)['compound'])
        df['negative'] = df['stemmed_text'].apply(lambda text: self.analyzer.polarity_scores(text)['neg'])
        df['neutral'] = df['stemmed_text'].apply(lambda text: self.analyzer.polarity_scores(text)['neu'])
        df['positive'] = df['stemmed_text'].apply(lambda text: self.analyzer.polarity_scores(text)['pos'])
        
        # Classify sentiments
        df['sentiment'] = 'neutral'
        df.loc[df['compound'] > 0.05, 'sentiment'] = 'positive'
        df.loc[df['compound'] < -0.05, 'sentiment'] = 'negative'
        
        logger.info("✓ Sentiment analysis completed")
        return df
    
    def get_sentiment_summary(self, df):
        """Get summary of sentiment analysis"""
        sentiment_counts = df['sentiment'].value_counts()
        majority_sentiment = sentiment_counts.idxmax()
        
        return sentiment_counts, majority_sentiment
    
    def get_top_negative_tweets(self, df, top_n=5):
        """Get top negative tweets by reply count"""
        negative_df = df[df['sentiment'] == 'negative'].copy()
        top_negative = negative_df.sort_values(by='reply_count', ascending=False).head(top_n)
        return top_negative
    
    def generate_sentiment_report(self, df):
        """Generate comprehensive sentiment report for Discord"""
        sentiment_counts, majority_sentiment = self.get_sentiment_summary(df)
        top_negative_tweets = self.get_top_negative_tweets(df)
        
        report += f"**📊 Overall Sentiment Distribution:**\n"
        report += f"✅ Positive: {sentiment_counts.get('positive', 0)}\n"
        report += f"❌ Negative: {sentiment_counts.get('negative', 0)}\n"
        report += f"⚪ Neutral: {sentiment_counts.get('neutral', 0)}\n\n"
        report += f"**🎯 Majority Sentiment:** {majority_sentiment.capitalize()}\n\n"
        
        if not top_negative_tweets.empty:
            report += "**🔻 Top 5 Negative Tweets (by replies):**\n"
            for index, row in top_negative_tweets.iterrows():
                tweet_text = row['full_text'][:100] + "..." if len(row['full_text']) > 100 else row['full_text']
                report += f"📊 {row['reply_count']} replies: {tweet_text}\n\n"
        
        return report