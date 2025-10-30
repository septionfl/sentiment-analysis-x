import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration class for environment variables"""
    
    # Twitter authentication
    TWITTER_AUTH_TOKEN = os.getenv('TWITTER_AUTH_TOKEN')
    
    # Discord configuration
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
    
    # Application settings
    DEFAULT_LIMIT = int(os.getenv('DEFAULT_LIMIT', 100))
    DEFAULT_FILENAME = os.getenv('DEFAULT_FILENAME', 'hasil_crawling.csv')
    DEFAULT_SEARCH_QUERY = os.getenv('DEFAULT_SEARCH_QUERY', 'from:tanyakanrl lang:id until:2024-10-29 since:2024-10-01')
    
    # Slang dictionary
    SLANG_DICT = {
        'wkwkwkkwkw': 'tertawa',
        'elu': 'kamu',
        'skrng': 'sekarang',
        'banyk': 'banyak',
        'bgt': 'banget',
        'kalo': 'kalau',
        'yg': 'yang',
        'mo': 'mau',
        'brapa': 'berapa',
        'ga': 'tidak',
        'udah': 'sudah',
        'lg': 'lagi',
        # ... (tambahkan semua slang words dari kode asli)
    }
    
    @classmethod
    def validate_config(cls):
        """Validate that required environment variables are set"""
        required_vars = ['TWITTER_AUTH_TOKEN', 'DISCORD_TOKEN']
        missing_vars = [var for var in required_vars if not getattr(cls, var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        print("✓ Configuration validated successfully")

# Validate configuration when module is imported
Config.validate_config()