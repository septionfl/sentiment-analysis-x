import discord
import asyncio
import pandas as pd
import re
import logging
import os
import sys
from datetime import datetime

# Import modules from the same package
from .config import Config
from .crawler import crawl_tweets
from .preprocessor import preprocess_data
from .translator import TextTranslator
from .analyzer import SentimentAnalyzer
from .visualizer import ResultVisualizer

logger = logging.getLogger(__name__)

class XSentimentBot:
    def __init__(self, token):
        self.token = token
        self.intents = discord.Intents.default()
        self.intents.message_content = True
        self.client = discord.Client(intents=self.intents)
        self.setup_handlers()
    
    def validate_twitter_query(self, query):
        """
        Validates and sanitizes Twitter search query
        """
        # Remove potentially dangerous characters but keep Twitter operators
        sanitized = re.sub(r'[^\w\s#@:\.\-"()]', '', query)
        return sanitized.strip()
    
    def parse_search_query(self, query):
        """
        Parses the search query and extracts components
        """
        # Basic validation
        if not query or len(query) > 500:
            return None, "Query terlalu panjang atau kosong. Maksimal 500 karakter."
        
        # Sanitize the query
        sanitized_query = self.validate_twitter_query(query)
        
        # Check if query contains at least some meaningful content
        meaningful_content = re.sub(r'(from:|since:|until:|lang:|\#|\@)\S+\s*', '', sanitized_query)
        meaningful_content = meaningful_content.strip()
        
        if not meaningful_content and not re.search(r'(from:|since:|until:|lang:)\S+', sanitized_query):
            return None, "Query harus mengandung kata kunci pencarian atau operator Twitter."
        
        return sanitized_query, None
    
    def get_help_text(self):
        """Generate help text for users"""
        return """
**🤖 X Sentiment Analysis Bot - Panduan Penggunaan**

**Perintah Utama:**
`@XS [query_pencarian]` - Analisis sentimen tweet berdasarkan query pencarian
`!help` atau `!bantuan` - Menampilkan pesan bantuan ini
`!example` atau `!contoh` - Contoh query pencarian
`!status` - Status bot dan informasi

**Format Query Pencarian:**
Gunakan format seperti **Twitter Advanced Search**:
- `@XS kata_kunci` - Pencarian sederhana
- `@XS "frasa exact"` - Pencarian frasa tepat
- `@XS #hashtag` - Pencarian berdasarkan hashtag
- `@XS from:username` - Tweet dari user tertentu
- `@XS since:YYYY-MM-DD until:YYYY-MM-DD` - Rentang waktu
- `@XS lang:id` - Tweet dalam bahasa Indonesia
- `@XS -keyword` - Mengecualikan keyword

**Contoh Penggunaan:**
`@XS #pemilu2024 since:2024-01-01 until:2024-02-14 lang:id`
`@XS "belajar coding" from:hacktiv8id`
`@XS kuliah online -webinar since:2023-09-01`
        """
    
    def get_examples_text(self):
        """Generate examples text for users"""
        return """
**📚 Contoh Query Pencarian yang Bisa Dicoba:**

1. **Trending Topic dengan Rentang Waktu**
   `@XS #pemilu2024 since:2024-02-01 until:2024-02-14 lang:id`

2. **Tweet dari Akun Spesifik**
   `@XS from:tanyakanrl since:2024-01-01 lang:id`

3. **Pencarian Frasa Exact**
   `@XS "krisis ekonomi" until:2024-02-14 lang:id`

4. **Pencarian dengan Eksklusi Keyword**
   `@XS startup -fail -bangkrut since:2023-01-01 lang:id`

5. **Kombinasi Kompleks**
   `@XS #teknologi from:startupdailyid since:2024-01-01 until:2024-02-14 -ai -robot`
        """
    
    def get_status_text(self):
        """Generate status text for the bot"""
        return """
**🔧 Status Bot**
- **Bot Name:** X Sentiment Analysis
- **Status:** ✅ Online
- **Usage:** Gunakan `@XS [query]` untuk menganalisis sentimen tweet

**📊 Fitur:**
✅ Crawling tweet real-time
✅ Preprocessing & pembersihan data
✅ Normalisasi bahasa slang Indonesia
✅ Terjemahan ke bahasa Inggris
✅ Analisis sentimen dengan VADER
✅ Laporan otomatis ke Discord
        """
    
    def setup_handlers(self):
        """Setup Discord event handlers"""
        
        @self.client.event
        async def on_ready():
            """Called when the bot is ready"""
            logger.info(f'Bot terhubung sebagai {self.client.user} (ID: {self.client.user.id})')
            print(f'✅ Bot logged in as {self.client.user}')
            
            # Set bot presence
            await self.client.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.listening,
                    name="@XS [search query]"
                )
            )
        
        @self.client.event
        async def on_message(message):
            """Handle incoming messages"""
            if message.author == self.client.user:
                return
            
            # Handle @XS command for sentiment analysis
            if message.content.startswith('@XS'):
                await self.handle_sentiment_analysis(message)
            
            # Handle help command
            elif message.content.startswith('!help') or message.content.startswith('!bantuan'):
                await message.channel.send(self.get_help_text())
            
            # Handle examples command
            elif message.content.startswith('!example') or message.content.startswith('!contoh'):
                await message.channel.send(self.get_examples_text())
            
            # Handle status command
            elif message.content.startswith('!status'):
                await message.channel.send(self.get_status_text())
            
            # Handle hello command
            elif message.content.startswith('!hello') or message.content.startswith('!halo'):
                await message.channel.send(f'👋 Halo {message.author.mention}! Saya adalah X Sentiment Analysis Bot. Gunakan `@XS [query]` untuk menganalisis sentimen tweet atau `!help` untuk bantuan.')
    
    async def handle_sentiment_analysis(self, message):
        """Handle sentiment analysis requests"""
        search_query = message.content[len('@XS'):].strip()
        
        # Check if query is empty
        if not search_query:
            await message.channel.send("❌ **Kesalahan Format**\n" + self.get_help_text())
            return
        
        # Validate the search query
        validated_query, error_msg = self.parse_search_query(search_query)
        
        if error_msg:
            await message.channel.send(f"❌ **Error Validasi Query:** {error_msg}")
            return
        
        # Initialize variables to avoid reference errors
        status_message = None
        df = pd.DataFrame()
        report = "Laporan tidak tersedia karena terjadi error selama proses analisis."
        
        try:
            # Send initial response
            initial_embed = discord.Embed(
                title="🔍 Memulai Analisis Sentimen",
                description=f"**Query:** `{validated_query}`",
                color=0x00ff00
            )
            initial_embed.add_field(name="Status", value="⏳ Memulai proses...", inline=False)
            initial_embed.set_footer(text="Proses mungkin memakan waktu beberapa menit")
            
            status_message = await message.channel.send(embed=initial_embed)
            
            # Step 1: Crawling tweets
            await self.update_status(status_message, "📥 Mengambil tweet...", 0.2)
            
            df = await asyncio.get_event_loop().run_in_executor(
                None, crawl_tweets, validated_query, None, 100
            )
            
            if df.empty:
                await self.update_status(status_message, "❌ Tidak ada tweet ditemukan", 1.0, False)
                await message.channel.send(f"❌ **Tidak ada tweet yang ditemukan untuk query:** `{validated_query}`\nCoba ubah kata kunci atau rentang waktu.")
                return
            
            # Step 2: Preprocessing
            await self.update_status(status_message, "🔄 Memproses data...", 0.4)
            df = await asyncio.get_event_loop().run_in_executor(None, preprocess_data, df)
            
            # Step 3: Translation
            await self.update_status(status_message, "🌐 Menerjemahkan teks...", 0.6)
            translator = TextTranslator()
            df = await asyncio.get_event_loop().run_in_executor(None, translator.process_translation, df)
            
            # Step 4: Sentiment Analysis
            await self.update_status(status_message, "📊 Menganalisis sentimen...", 0.8)
            analyzer = SentimentAnalyzer()
            df = await asyncio.get_event_loop().run_in_executor(None, analyzer.analyze_sentiment, df)
            
            # Step 5: Generate results
            await self.update_status(status_message, "📈 Menyusun laporan...", 0.9)
            
            # Generate report with error handling
            try:
                report = analyzer.generate_sentiment_report(df)
            except Exception as report_error:
                logger.error(f"Error generating report: {report_error}")
                report = f"❌ Error saat menghasilkan laporan detail: {str(report_error)}"
            
            # Save results locally
            visualizer = ResultVisualizer()
            safe_query_name = "".join(x for x in validated_query[:30] if x.isalnum() or x in (' ', '-', '_')).rstrip()
            output_filename = f"results/sentiment_{safe_query_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            visualizer.save_results(df, output_filename)
            
            # Send completion status
            await self.update_status(status_message, "✅ Analisis selesai!", 1.0, True)
            
            # Send results embed
            results_embed = discord.Embed(
                title="📊 Hasil Analisis Sentimen",
                description=f"**Query:** `{validated_query}`",
                color=0x0099ff,
                timestamp=datetime.now()
            )
            
            sentiment_counts, majority_sentiment = analyzer.get_sentiment_summary(df)
            
            results_embed.add_field(
                name="📈 Distribusi Sentimen",
                value=f"✅ **Positive:** {sentiment_counts.get('positive', 0)}\n❌ **Negative:** {sentiment_counts.get('negative', 0)}\n⚪ **Neutral:** {sentiment_counts.get('neutral', 0)}",
                inline=True
            )
            
            results_embed.add_field(
                name="🎯 Sentimen Mayoritas",
                value=f"**{majority_sentiment.capitalize()}**",
                inline=True
            )
            
            results_embed.add_field(
                name="📊 Total Tweet",
                value=f"**{len(df)}** tweet dianalisis",
                inline=True
            )
            
            # Add top negative tweets if any
            top_negative = analyzer.get_top_negative_tweets(df)
            if not top_negative.empty:
                negative_text = ""
                for i, (idx, row) in enumerate(top_negative.iterrows(), 1):
                    tweet_preview = row['full_text'][:80] + "..." if len(row['full_text']) > 80 else row['full_text']
                    negative_text += f"{i}. ({row['reply_count']} replies) {tweet_preview}\n"
                
                # Ensure we don't exceed Discord's field value limit
                if len(negative_text) > 1024:
                    negative_text = negative_text[:1021] + "..."
                
                results_embed.add_field(
                    name="🔻 Top Negative Tweets",
                    value=negative_text,
                    inline=False
                )
            
            results_embed.set_footer(text=f"Analisis untuk {message.author.display_name}")
            
            await message.channel.send(embed=results_embed)
            
            # Send detailed report
            if len(report) < 2000:
                await message.channel.send(f"**📋 Laporan Detail:**\n{report}")
            else:
                # If report is too long, send a shortened version
                shortened_report = report[:1997] + "..."
                await message.channel.send(f"**📋 Laporan Detail:**\n{shortened_report}")
            
            logger.info(f"Successfully completed analysis for user {message.author.name}: {validated_query}")
            
        except Exception as e:
            logger.error(f"Error processing sentiment analysis for {message.author.name}: {str(e)}")
            
            # Create error message
            error_message = f"❌ **Error selama analisis sentimen**\n\n**Query:** `{validated_query}`\n\n**Error:** ```{str(e)}```\n\nSilakan coba lagi dengan query yang berbeda atau hubungi administrator."
            
            # Try to update status message if it exists
            if status_message:
                try:
                    await self.update_status(status_message, f"❌ Error: {str(e)[:50]}...", 1.0, False)
                except Exception as update_error:
                    logger.error(f"Error updating status: {update_error}")
            
            await message.channel.send(error_message)
    
    async def update_status(self, message, status, progress, success=None):
        """Update the status message with progress"""
        try:
            # Create progress bar
            bars = 10
            filled_bars = int(bars * progress)
            progress_bar = "█" * filled_bars + "▒" * (bars - filled_bars)
            
            # Determine color based on success
            color = 0x00ff00 if success is True else 0xff0000 if success is False else 0xffff00
            
            embed = discord.Embed(
                title="🔍 Analisis Sentimen dalam Progress",
                description=f"**Status:** {status}",
                color=color
            )
            embed.add_field(name="Progress", value=f"`[{progress_bar}] {int(progress*100)}%`", inline=False)
            
            await message.edit(embed=embed)
            
        except Exception as e:
            logger.error(f"Error updating status: {e}")
    
    def run(self):
        """Run the Discord bot"""
        try:
            logger.info("Starting Discord bot...")
            self.client.run(self.token)
        except discord.errors.LoginFailure:
            logger.error("❌ Login failed. Please check your Discord token in the .env file.")
            print("❌ ERROR: Invalid Discord token. Please check your .env file.")
        except Exception as e:
            logger.error(f"❌ Error running Discord bot: {e}")
            print(f"❌ ERROR: {e}")

# For testing purposes
if __name__ == "__main__":
    # This allows testing the bot directly
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Setup basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("❌ ERROR: DISCORD_TOKEN not found in environment variables")
        exit(1)
    
    bot = XSentimentBot(token)
    bot.run()