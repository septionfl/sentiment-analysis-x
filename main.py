import os
import sys
import logging
from dotenv import load_dotenv

# Fix Windows encoding issues
if sys.platform.startswith('win'):
    # Set UTF-8 encoding for Windows console
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    
    # Fix for Windows console encoding
    try:
        import win32console
        # Try to set console output to UTF-8
        win32console.SetConsoleOutputCP(65001)
    except ImportError:
        pass

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables
load_dotenv()

from src.crawler import install_dependencies, crawl_tweets, check_node_installation
from src.preprocessor import preprocess_data
from src.translator import TextTranslator
from src.analyzer import SentimentAnalyzer
from src.visualizer import ResultVisualizer
from src.discord_bot import XSentimentBot
from src.config import Config

def setup_logging():
    """Setup logging configuration with Windows encoding fix"""
    # Create formatter without emojis for Windows
    if sys.platform.startswith('win'):
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))
    
    # Clear any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Add console handler with proper encoding
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Add file handler with UTF-8 encoding
    file_handler = logging.FileHandler('sentiment_analysis.log', encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

def run_sentiment_analysis(custom_query=None):
    """Run standard sentiment analysis with optional custom query"""
    logger = logging.getLogger(__name__)
    logger.info("Starting Twitter Sentiment Analysis...")
    
    try:
        # Check Node.js installation first
        if not check_node_installation():
            logger.error("❌ Please install Node.js first from https://nodejs.org/")
            return
        
        # Use custom query if provided
        search_query = custom_query if custom_query else Config.DEFAULT_SEARCH_QUERY
        logger.info(f"Using search query: {search_query}")
        
        df = crawl_tweets(search_keyword=search_query)
        
        if df.empty:
            logger.error("❌ No tweets found. Exiting.")
            return
        
        # Continue with processing...
        df = preprocess_data(df)
        
        translator = TextTranslator()
        df = translator.process_translation(df)
        
        analyzer = SentimentAnalyzer()
        df = analyzer.analyze_sentiment(df)
        
        visualizer = ResultVisualizer()
        
        sentiment_counts, majority_sentiment = analyzer.get_sentiment_summary(df)
        logger.info("Sentiment Distribution: %s", sentiment_counts.to_dict())
        
        filename_safe = "".join(x for x in search_query[:50] if x.isalnum() or x in (' ', '-', '_')).rstrip()
        output_filename = f"results/sentiment_{filename_safe}.csv"
        
        visualizer.save_results(df, output_filename)
        
        report = analyzer.generate_sentiment_report(df)
        logger.info("Analysis completed successfully")
        
        print("\n" + "="*50)
        print("SENTIMENT ANALYSIS RESULTS")
        print("="*50)
        print(report)
        
        visualizer.send_to_discord_webhook(report)
        
        return df
        
    except Exception as e:
        logger.error(f"Error during sentiment analysis: {e}")
        raise

def run_discord_bot():
    """Run Discord bot"""
    logger = logging.getLogger(__name__)
    logger.info("Starting Discord Bot...")
    
    # Check Node.js installation first
    if not check_node_installation():
        logger.error("❌ Please install Node.js first from https://nodejs.org/")
        return
    
    try:
        bot = XSentimentBot(Config.DISCORD_TOKEN)
        bot.run()
    except Exception as e:
        logger.error(f"Error running Discord bot: {e}")
        raise

def main():
    """Main function with mode selection"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Create necessary directories
    os.makedirs("tweets-data", exist_ok=True)
    os.makedirs("results", exist_ok=True)
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode == 'bot':
            run_discord_bot()
        elif mode == 'analysis':
            custom_query = sys.argv[2] if len(sys.argv) > 2 else None
            run_sentiment_analysis(custom_query)
        elif mode == 'install':
            if install_dependencies():
                logger.info("✅ Dependencies installed successfully")
            else:
                logger.error("❌ Failed to install dependencies")
        elif mode == 'check':
            check_node_installation()
        else:
            print("Usage: python main.py [bot|analysis|install|check] [query]")
            print("  bot                    - Run Discord bot")
            print("  analysis \"query\"       - Run one-time sentiment analysis")
            print("  install                - Install Node.js dependencies")
            print("  check                  - Check Node.js installation")
            print("\nContoh: python main.py analysis \"#pemilu2024\"")
    else:
        # Default: run analysis with default query
        run_sentiment_analysis()

if __name__ == "__main__":
    main()