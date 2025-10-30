import matplotlib.pyplot as plt
import pandas as pd
import requests
import logging
from .config import Config

logger = logging.getLogger(__name__)

class ResultVisualizer:
    @staticmethod
    def plot_sentiment_distribution(sentiment_counts, save_path=None):
        """Plot sentiment distribution"""
        plt.figure(figsize=(8, 6))
        sentiment_counts.plot(kind='bar', color=['skyblue', 'lightgreen', 'salmon'])
        plt.title('Sentiment Distribution of Tweets')
        plt.xlabel('Sentiment')
        plt.ylabel('Number of Tweets')
        plt.xticks(rotation=0)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
            logger.info(f"✓ Plot saved to {save_path}")
        else:
            plt.show()
    
    @staticmethod
    def save_results(df, filename='sentiment_analysis_results.csv'):
        """Save results to CSV"""
        df.to_csv(filename, index=False)
        logger.info(f"✓ Results saved to {filename}")
    
    @staticmethod
    def display_sample_tweets(df, sentiment=None, n=5):
        """Display sample tweets based on sentiment"""
        if sentiment:
            sample_df = df[df['sentiment'] == sentiment].copy().head(n)
            print(f"\n{sentiment.capitalize()} Tweets:")
        else:
            sample_df = df.head(n)
            print(f"\nSample Tweets:")
        
        print(sample_df[['full_text', 'sentiment']].to_string())
    
    @staticmethod
    def send_to_discord_webhook(message):
        """Send message to Discord webhook"""
        if not Config.DISCORD_WEBHOOK_URL:
            logger.warning("Discord webhook URL not configured")
            return
        
        message_payload = {
            'content': message
        }
        
        try:
            response = requests.post(Config.DISCORD_WEBHOOK_URL, json=message_payload)
            response.raise_for_status()
            if response.status_code == 204:
                logger.info("✓ Message successfully sent to Discord")
            else:
                logger.warning(f"Unexpected status code from Discord: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending message to Discord: {e}")