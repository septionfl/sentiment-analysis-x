from googletrans import Translator
import time
import nltk
import logging
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

logger = logging.getLogger(__name__)

def download_stopwords():
    """Download NLTK stopwords if not available"""
    try:
        stopwords.words('english')
    except LookupError:
        logger.info("Downloading NLTK stopwords...")
        nltk.download('stopwords')

class TextTranslator:
    def __init__(self):
        self.translator = Translator()
        self.porter = PorterStemmer()
        download_stopwords()
        self.english_stopwords = set(stopwords.words('english'))
        logger.info("✓ Text translator initialized")
    
    def translate_tokens_to_english(self, tokens):
        """Translate tokens from Indonesian to English"""
        text = " ".join(tokens)
        try:
            translated_text = self.translator.translate(text, src='id', dest='en').text
            time.sleep(1)  # Rate limiting
            return translated_text
        except Exception as e:
            logger.warning(f"Translation failed for text: {text}. Error: {e}")
            return text
    
    def remove_stopwords(self, tokens):
        """Remove English stopwords"""
        return [word for word in tokens if word not in self.english_stopwords]
    
    def stem_tokens(self, tokens):
        """Apply stemming to tokens"""
        return [self.porter.stem(word) for word in tokens]
    
    def process_translation(self, df):
        """Main translation processing function"""
        logger.info("Translating text to English...")
        df['translated_text'] = df['tokens'].apply(self.translate_tokens_to_english)
        
        logger.info("Processing translated text...")
        df['translated_tokens'] = df['translated_text'].apply(word_tokenize)
        df['translated_tokens'] = df['translated_tokens'].apply(self.remove_stopwords)
        df['stemmed_tokens'] = df['translated_tokens'].apply(self.stem_tokens)
        df['stemmed_text'] = df['stemmed_tokens'].apply(lambda tokens: ' '.join(tokens))
        
        logger.info("✓ Text translation and processing completed")
        return df