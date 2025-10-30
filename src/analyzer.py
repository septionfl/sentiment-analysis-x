import nltk
import logging
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import pandas as pd
from collections import Counter
import re

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
    
    def get_sentiment_insights(self, df):
        """Generate detailed insights for each sentiment category"""
        insights = {
            'positive': {'tweets': [], 'common_words': [], 'avg_engagement': 0},
            'negative': {'tweets': [], 'common_words': [], 'avg_engagement': 0},
            'neutral': {'tweets': [], 'common_words': [], 'avg_engagement': 0}
        }
        
        # Analyze each sentiment category
        for sentiment in ['positive', 'negative', 'neutral']:
            sentiment_df = df[df['sentiment'] == sentiment].copy()
            
            if not sentiment_df.empty:
                # Get sample tweets (up to 3)
                insights[sentiment]['tweets'] = sentiment_df.nlargest(3, 'reply_count')[['full_text', 'reply_count']].to_dict('records')
                
                all_text = ' '.join(sentiment_df['full_text'].astype(str)).lower()
                words = re.findall(r'\b\w+\b', all_text)
                # Filter out common stop words and short words
                stop_words = {'yang', 'di', 'dan', 'itu', 'dengan', 'untuk', 'dari', 'ini', 'pada', 'tidak', 'akan', 'saya', 'kita', 'ke', 'dalam', 'ada', 'atau', 'juga', 'the', 'and', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'as', 'by', 'is', 'are', 'was', 'were', 'be', 'this', 'that', 'it', 'he', 'she', 'they', 'we', 'you', 'i', 'me', 'him', 'her', 'them', 'us', 'my', 'your', 'his', 'her', 'its', 'our', 'their'}
                filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
                common_words = Counter(filtered_words).most_common(5)
                insights[sentiment]['common_words'] = [word for word, count in common_words]
                
                # Calculate average engagement
                insights[sentiment]['avg_engagement'] = sentiment_df['reply_count'].mean()
        
        return insights
    
    def generate_sentiment_report(self, df):
        """Generate comprehensive sentiment report"""
        sentiment_counts, majority_sentiment = self.get_sentiment_summary(df)
        insights = self.get_sentiment_insights(df)
        
        report = f"**📊 Sentiment Analysis Report**\n\n"
        report += f"**Overall Sentiment Distribution:**\n"
        report += f"✅ Positive: {sentiment_counts.get('positive', 0)}\n"
        report += f"❌ Negative: {sentiment_counts.get('negative', 0)}\n"
        report += f"⚪ Neutral: {sentiment_counts.get('neutral', 0)}\n\n"
        report += f"**🎯 Majority Sentiment:** {majority_sentiment.capitalize()}\n\n"
        
        # Add insights for each sentiment
        report += "**🔍 Detailed Insights:**\n\n"
        
        # Positive insights
        report += "✅ **Positive Sentiment Insights:**\n"
        if insights['positive']['common_words']:
            report += f"• Top keywords: {', '.join(insights['positive']['common_words'])}\n"
            report += f"• Avg engagement: {insights['positive']['avg_engagement']:.1f} replies/tweet\n"
        else:
            report += "• No significant positive tweets found\n"
        report += "\n"
        
        # Negative insights
        report += "❌ **Negative Sentiment Insights:**\n"
        if insights['negative']['common_words']:
            report += f"• Top keywords: {', '.join(insights['negative']['common_words'])}\n"
            report += f"• Avg engagement: {insights['negative']['avg_engagement']:.1f} replies/tweet\n"
        else:
            report += "• No significant negative tweets found\n"
        report += "\n"
        
        # Neutral insights
        report += "⚪ **Neutral Sentiment Insights:**\n"
        if insights['neutral']['common_words']:
            report += f"• Top keywords: {', '.join(insights['neutral']['common_words'])}\n"
            report += f"• Avg engagement: {insights['neutral']['avg_engagement']:.1f} replies/tweet\n"
        else:
            report += "• No significant neutral tweets found\n"
        
        return report