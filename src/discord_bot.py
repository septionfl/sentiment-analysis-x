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
from .smart_crawler import SmartCrawler

logger = logging.getLogger(__name__)

class XSentimentBot:
    def __init__(self, token):
        self.token = token
        self.intents = discord.Intents.default()
        self.intents.message_content = True
        self.client = discord.Client(intents=self.intents)
        self.smart_crawler = SmartCrawler()
        self.setup_handlers()
    
    def is_twitter_advanced_query(self, text):
        """
        Check if the text already contains Twitter advanced search operators
        """
        twitter_operators = [
            'from:', 'since:', 'until:', 'lang:', 'filter:', 
            ' -', '#', '@', '"', '?', ' OR ', ' AND '
        ]
        return any(operator in text for operator in twitter_operators)
    
    def validate_query(self, query):
        """
        Validates and sanitizes search query
        """
        if not query or len(query) > 500:
            return None, "Query terlalu panjang atau kosong. Maksimal 500 karakter."
        
        # Sanitize the query - allow Twitter operators and common characters
        sanitized = re.sub(r'[^\w\s#@:\.\-"()?]', '', query)
        sanitized = sanitized.strip()
        
        if not sanitized:
            return None, "Query tidak valid."
        
        return sanitized, None
    
    def get_help_text(self):
        """Generate help text for users"""
        return """
**🤖 X Sentiment Analysis Bot - Panduan Penggunaan**

**Perintah Utama:**
`@XS [query]` - Analisis sentimen tweet (mendukung natural language & advanced search)

**Format Input yang Didukung:**

**1. Natural Language (AI-Powered):**
- `@XS sentimen tentang pemilu 2024`
- `@XS tweet dari jokowi bulan januari`
- `@XS opini masyarakat tentang krisis ekonomi`

**2. Twitter Advanced Search:**
- `@XS #pemilu2024 since:2024-01-01 until:2024-02-14 lang:id`
- `@XS from:tanyakanrl since:2024-01-01 lang:id`
- `@XS "belajar coding" from:hacktiv8id`

**Fitur Laporan:**
✅ Insight detail untuk setiap sentimen (positif, negatif, netral)
✅ 5 tweet negatif dengan replies terbanyak (tampilan lengkap)
✅ Analisis kata kunci untuk setiap kategori sentimen
✅ Rata-rata engagement per kategori

**Perintah Bantuan:**
`!help` atau `!bantuan` - Menampilkan pesan bantuan ini
`!example` atau `!contoh` - Contoh query pencarian
`!status` - Status bot dan informasi
        """
    
    def get_examples_text(self):
        """Generate examples text for users"""
        return """
**📚 Contoh Penggunaan @XS:**

**🌐 Natural Language:**
`@XS sentimen masyarakat tentang pemilu 2024`
`@XS tweet dari presiden jokowi bulan januari 2024`
`@XS opini tentang startup teknologi di Indonesia`
`@XS bagaimana respons twitter tentang krisis ekonomi`

**🔍 Advanced Search:**
`@XS #pemilu2024 since:2024-02-01 until:2024-02-14 lang:id`
`@XS from:tanyakanrl since:2024-01-01 lang:id`
`@XS "krisis ekonomi" until:2024-02-14 lang:id`
`@XS startup -fail -bangkrut since:2023-01-01 lang:id`
        """
    
    def get_status_text(self):
        """Generate status text for the bot"""
        groq_status = "✅ Active" if os.getenv('GROQ_API_KEY') else "❌ Not configured"
        
        return f"""
**🔧 Status Bot**
- **Bot Name:** X Sentiment Analysis AI
- **Status:** ✅ Online
- **GROQ AI:** {groq_status}
- **Command:** `@XS [query]`

**🚀 Fitur Baru:**
✅ Insight detail per kategori sentimen
✅ Tampilan lengkap 5 tweet negatif teratas
✅ Analisis kata kunci per sentimen
✅ Rata-rata engagement metrics
✅ AI-Powered query parsing
✅ Multi-strategy fallback
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
                    name="@XS [query]"
                )
            )
        
        @self.client.event
        async def on_message(message):
            """Handle incoming messages"""
            if message.author == self.client.user:
                return
            
            # Handle @XS command for unified sentiment analysis
            if message.content.startswith('@XS'):
                await self.handle_unified_analysis(message)
            
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
                await message.channel.send(
                    f'👋 Halo {message.author.mention}! Saya adalah X Sentiment Analysis Bot. '
                    f'Gunakan `@XS [query]` untuk menganalisis sentimen tweet dengan insight detail per kategori!'
                )
    
    async def handle_unified_analysis(self, message):
        """Handle unified sentiment analysis that supports all input types"""
        user_input = message.content[len('@XS'):].strip()
        
        # Check if query is empty
        if not user_input:
            await message.channel.send("❌ **Kesalahan Format**\n" + self.get_help_text())
            return
        
        # Validate the query
        validated_input, error_msg = self.validate_query(user_input)
        
        if error_msg:
            await message.channel.send(f"❌ **Error Validasi:** {error_msg}")
            return
        
        # Determine input type and process accordingly
        if self.is_twitter_advanced_query(validated_input):
            await self.process_advanced_search(message, validated_input)
        else:
            await self.process_natural_language(message, validated_input)
    
    async def process_natural_language(self, message, user_input):
        """Process natural language input with AI-powered parsing"""
        status_message = None
        df = pd.DataFrame()
        
        try:
            # Send initial response for AI mode
            initial_embed = discord.Embed(
                title="🤖 Memulai Analisis",
                description=f"**Input:** `{user_input}`",
                color=0x9b59b6  # Purple color for AI mode
            )
            initial_embed.add_field(name="Mode", value="🌐 Natural Language Processing", inline=False)
            initial_embed.add_field(name="Status", value="⏳ Memproses bahasa natural...", inline=False)
            initial_embed.set_footer(text="Menggunakan GROQ AI untuk parsing query...")
            
            status_message = await message.channel.send(embed=initial_embed)
            
            # Step 1: AI-Powered Query Parsing
            await self.update_status(status_message, "🧠 Parsing bahasa natural...", 0.2)
            
            smart_result = await asyncio.get_event_loop().run_in_executor(
                None, self.smart_crawler.smart_search, user_input
            )
            
            if not smart_result['success']:
                await self.update_status(status_message, "❌ AI parsing gagal", 1.0, False)
                
                # Provide helpful error message with fallback suggestion
                error_embed = discord.Embed(
                    title="❌ Analisis Gagal",
                    description=f"**Input:** `{user_input}`",
                    color=0xff0000
                )
                error_embed.add_field(
                    name="Kemungkinan Penyebab", 
                    value="• Query terlalu kompleks\n• Tidak ada tweet ditemukan\n• Server sibuk",
                    inline=False
                )
                error_embed.add_field(
                    name="Saran", 
                    value="Coba gunakan format advanced search:\n`@XS #hashtag since:2024-01-01 lang:id`",
                    inline=False
                )
                
                await message.channel.send(embed=error_embed)
                return
            
            used_query = smart_result['used_query']
            df = smart_result['data']
            
            # Continue with processing
            await self.process_tweet_data(message, status_message, df, user_input, used_query, "AI-Powered")
            
        except Exception as e:
            await self.handle_processing_error(message, status_message, user_input, e, "AI-Powered")
    
    async def process_advanced_search(self, message, user_input):
        """Process advanced search query directly"""
        status_message = None
        df = pd.DataFrame()
        
        try:
            # Send initial response for advanced search mode
            initial_embed = discord.Embed(
                title="🔍 Memulai Analisis Advanced Search",
                description=f"**Query:** `{user_input}`",
                color=0x3498db  # Blue color for advanced search
            )
            initial_embed.add_field(name="Mode", value="🔍 Twitter Advanced Search", inline=False)
            initial_embed.add_field(name="Status", value="⏳ Memulai proses...", inline=False)
            initial_embed.set_footer(text="Menggunakan query Twitter langsung...")
            
            status_message = await message.channel.send(embed=initial_embed)
            
            # Step 1: Direct crawling with advanced query
            await self.update_status(status_message, "📥 Mengambil tweet...", 0.2)
            
            df = await asyncio.get_event_loop().run_in_executor(
                None, crawl_tweets, user_input, None, 100
            )
            
            if df.empty:
                await self.update_status(status_message, "❌ Tidak ada tweet ditemukan", 1.0, False)
                
                # Provide suggestions for advanced query
                error_embed = discord.Embed(
                    title="❌ Tidak Ada Tweet Ditemukan",
                    description=f"**Query:** `{user_input}`",
                    color=0xff0000
                )
                error_embed.add_field(
                    name="Saran Perbaikan", 
                    value="• Perluas rentang waktu\n• Kurangi filter\n• Coba keyword yang lebih umum\n• Gunakan natural language: `@XS [deskripsi]`",
                    inline=False
                )
                
                await message.channel.send(embed=error_embed)
                return
            
            # Continue with processing
            await self.process_tweet_data(message, status_message, df, user_input, user_input, "Advanced Search")
            
        except Exception as e:
            await self.handle_processing_error(message, status_message, user_input, e, "Advanced Search")
    
    async def process_tweet_data(self, message, status_message, df, original_input, used_query, mode):
        """Process tweet data through the analysis pipeline"""
        try:
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
            
            # Save results locally
            visualizer = ResultVisualizer()
            safe_query_name = "".join(x for x in original_input[:30] if x.isalnum() or x in (' ', '-', '_')).rstrip()
            output_filename = f"results/sentiment_{safe_query_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            visualizer.save_results(df, output_filename)
            
            # Send completion status
            await self.update_status(status_message, "✅ Analisis selesai!", 1.0, True)
            
            # Send results embed with insights
            await self.send_insights_embed(message, original_input, used_query, mode, analyzer, df)
            
            # Send top negative tweets in separate messages
            await self.send_negative_tweets(message, analyzer, df)
            
            logger.info(f"Successfully completed {mode.lower()} analysis for user {message.author.name}: {original_input}")
            
        except Exception as e:
            raise e
    
    async def send_insights_embed(self, message, original_input, used_query, mode, analyzer, df):
        """Send the insights embed to Discord"""
        # Determine color based on mode
        color = 0x9b59b6 if "AI" in mode else 0x3498db
        
        # Get sentiment summary and insights
        sentiment_counts, majority_sentiment = analyzer.get_sentiment_summary(df)
        insights = analyzer.get_sentiment_insights(df)
        
        results_embed = discord.Embed(
            title="📊 Hasil Analisis Sentimen - Insights Detail",
            description=f"**Input:** `{original_input}`",
            color=color,
            timestamp=datetime.now()
        )
        
        # Add mode information
        results_embed.add_field(
            name="🚀 Mode Analisis",
            value=mode,
            inline=False
        )
        
        # If AI mode and query was optimized, show the optimized query
        if "AI" in mode and used_query != original_input:
            results_embed.add_field(
                name="🔮 Query yang Digunakan",
                value=f"`{used_query}`",
                inline=False
            )
        
        # Sentiment distribution
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
        
        # Positive insights
        positive_insight = f"**Kata kunci:** {', '.join(insights['positive']['common_words']) if insights['positive']['common_words'] else 'Tidak ada'}\n"
        positive_insight += f"**Engagement:** {insights['positive']['avg_engagement']:.1f} replies/tweet"
        results_embed.add_field(
            name="✅ Insight Positif",
            value=positive_insight,
            inline=False
        )
        
        # Negative insights
        negative_insight = f"**Kata kunci:** {', '.join(insights['negative']['common_words']) if insights['negative']['common_words'] else 'Tidak ada'}\n"
        negative_insight += f"**Engagement:** {insights['negative']['avg_engagement']:.1f} replies/tweet"
        results_embed.add_field(
            name="❌ Insight Negatif",
            value=negative_insight,
            inline=False
        )
        
        # Neutral insights
        neutral_insight = f"**Kata kunci:** {', '.join(insights['neutral']['common_words']) if insights['neutral']['common_words'] else 'Tidak ada'}\n"
        neutral_insight += f"**Engagement:** {insights['neutral']['avg_engagement']:.1f} replies/tweet"
        results_embed.add_field(
            name="⚪ Insight Netral",
            value=neutral_insight,
            inline=False
        )
        
        results_embed.set_footer(text=f"Analisis untuk {message.author.display_name}")
        
        await message.channel.send(embed=results_embed)
    
    async def send_negative_tweets(self, message, analyzer, df):
        """Send top 5 negative tweets with full text in separate messages"""
        top_negative = analyzer.get_top_negative_tweets(df)
        
        if not top_negative.empty:
            # Send header for negative tweets
            header_embed = discord.Embed(
                title="🔻 5 Tweet Negatif dengan Replies Terbanyak",
                description="Berikut adalah tweet-tweet negatif yang mendapat engagement tertinggi:",
                color=0xff6b6b
            )
            await message.channel.send(embed=header_embed)
            
            # Send each negative tweet in a separate embed
            for i, (idx, row) in enumerate(top_negative.iterrows(), 1):
                tweet_embed = discord.Embed(
                    title=f"Tweet Negatif #{i}",
                    description=f"**Reply Count:** {row['reply_count']}",
                    color=0xff6b6b,
                    timestamp=datetime.now()
                )
                
                # Add the full tweet text (Discord has a 4096 character limit for embed descriptions)
                tweet_text = row['full_text']
                if len(tweet_text) > 4096:
                    tweet_text = tweet_text[:4093] + "..."
                
                tweet_embed.add_field(
                    name="📝 Isi Tweet",
                    value=tweet_text,
                    inline=False
                )
                
                # Add additional metrics if available
                if 'like_count' in row and pd.notna(row['like_count']):
                    tweet_embed.add_field(
                        name="❤️ Likes",
                        value=row['like_count'],
                        inline=True
                    )
                
                if 'retweet_count' in row and pd.notna(row['retweet_count']):
                    tweet_embed.add_field(
                        name="🔄 Retweets",
                        value=row['retweet_count'],
                        inline=True
                    )
                
                await message.channel.send(embed=tweet_embed)
                
                # Add a small delay between messages to avoid rate limiting
                await asyncio.sleep(0.5)
        else:
            no_negative_embed = discord.Embed(
                title="✅ Tidak Ada Tweet Negatif",
                description="Tidak ditemukan tweet dengan sentimen negatif dalam hasil analisis.",
                color=0x00ff00
            )
            await message.channel.send(embed=no_negative_embed)
    
    async def handle_processing_error(self, message, status_message, user_input, error, mode):
        """Handle processing errors"""
        logger.error(f"Error processing {mode} analysis for {message.author.name}: {str(error)}")
        
        # Create error message
        error_message = f"❌ **Error selama analisis {mode}**\n\n**Input:** `{user_input}`\n\n**Error:** ```{str(error)[:500]}```\n\nSilakan coba lagi dengan input yang berbeda."
        
        # Try to update status message if it exists
        if status_message:
            try:
                await self.update_status(status_message, f"❌ Error: {str(error)[:50]}...", 1.0, False)
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
            
            # Get current embed and update it
            current_embed = message.embeds[0] if message.embeds else None
            if current_embed:
                # Find and update the status field
                updated_fields = []
                for field in current_embed.fields:
                    if field.name == "Status":
                        updated_fields.append(("Status", status, False))
                    else:
                        updated_fields.append((field.name, field.value, field.inline))
                
                # Rebuild embed
                new_embed = discord.Embed(
                    title=current_embed.title,
                    description=current_embed.description,
                    color=color
                )
                
                for name, value, inline in updated_fields:
                    new_embed.add_field(name=name, value=value, inline=inline)
                
                new_embed.add_field(name="Progress", value=f"`[{progress_bar}] {int(progress*100)}%`", inline=False)
                new_embed.set_footer(text=current_embed.footer.text)
                
                await message.edit(embed=new_embed)
            else:
                # Fallback if no embed exists
                embed = discord.Embed(
                    title="🔍 Analisis dalam Progress",
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