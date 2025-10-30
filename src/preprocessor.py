import re
import nltk
import logging
from nltk.tokenize import word_tokenize
from .config import Config

logger = logging.getLogger(__name__)

def download_nltk_resources():
    """Download required NLTK resources"""
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        logger.info("Downloading NLTK punkt resources...")
        nltk.download('punkt_tab')

def clean_text(df):
    """Clean the text data"""
    logger.info("Cleaning text data...")
    
    df['full_text'] = df['full_text'].fillna('')
    df = df.drop_duplicates(subset=['full_text'])
    df['full_text'] = df['full_text'].str.lower()
    
    # Remove URLs, mentions, hashtags, and punctuation
    df['full_text'] = df['full_text'].apply(lambda x: re.sub(r'http\S+|www\S+|https\S+', '', x, flags=re.MULTILINE))
    df['full_text'] = df['full_text'].apply(lambda x: re.sub(r'@\w+', '', x))
    df['full_text'] = df['full_text'].apply(lambda x: re.sub(r'#\w+', '', x))
    df['full_text'] = df['full_text'].apply(lambda x: re.sub(r'[^\w\s]', '', x))
    
    return df

def tokenize_text(df):
    """Tokenize the text"""
    logger.info("Tokenizing text...")
    df['tokens'] = df['full_text'].apply(word_tokenize)
    return df

def normalize_slang(tokens, slang_dictionary):
    """Normalize slang words"""
    return [slang_dictionary.get(token, token) for token in tokens]

def apply_slang_normalization(df):
    """Apply slang normalization to tokens"""
    logger.info("Normalizing slang words...")
    df['tokens'] = df['tokens'].apply(lambda tokens: normalize_slang(tokens, Config.SLANG_DICT))
    return df

def preprocess_data(df):
    """Main preprocessing function"""
    download_nltk_resources()
    df = clean_text(df)
    df = tokenize_text(df)
    df = apply_slang_normalization(df)
    logger.info("✓ Text preprocessing completed")
    return df