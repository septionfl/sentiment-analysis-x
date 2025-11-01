# 🤖 X Sentiment Analysis AI

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Discord.py](https://img.shields.io/badge/Discord.py-2.3+-7289da.svg)](https://discord.py)
[![GROQ AI](https://img.shields.io/badge/GROQ-AI%20Powered-00ff00.svg)](https://groq.com)
[![Twitter](https://img.shields.io/badge/Twitter-API-1da1f2.svg)](https://twitter.com)

**AI-powered sentiment analysis bot for Twitter/X with natural language understanding**

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Configuration](#-configuration) • [Examples](#-examples)

</div>

## 🌟 Overview

X Sentiment Analysis AI is a powerful Discord bot that performs real-time sentiment analysis on Twitter/X data. It features **AI-powered natural language query parsing** using GROQ API, allowing users to search tweets using everyday language instead of complex search operators.

### 🎯 What Makes This Unique?

- **🤖 AI-Powered Queries**: Convert natural language to optimized Twitter search queries
- **📊 Detailed Insights**: Comprehensive sentiment analysis with per-category insights
- **🔍 Flexible Search**: Supports both natural language and advanced Twitter search syntax
- **💫 Smart Fallbacks**: Multiple search strategies when initial queries fail
- **🌐 Multi-language**: Automatic Indonesian slang normalization and translation

---

## 🚀 Features

### 🤖 AI-Powered Intelligence
- **Natural Language Processing**: Ask in plain language - "sentimen tentang pemilu 2024"
- **GROQ AI Integration**: Advanced query optimization using Llama models
- **Smart Query Validation**: AI-powered complexity analysis and suggestions
- **Automatic Mode Detection**: Intelligently detects query type

### 📊 Advanced Analytics
- **Per-Sentiment Insights**: Detailed analysis for positive, negative, and neutral categories
- **Keyword Analysis**: Top keywords for each sentiment category
- **Engagement Metrics**: Average replies, likes, and retweets per sentiment
- **Full Tweet Display**: Complete negative tweets with highest engagement

### 🔧 Technical Excellence
- **Multi-Strategy Crawling**: Adaptive fallback when searches fail
- **Real-time Processing**: Live progress updates with visual progress bars
- **Data Export**: Automatic CSV saving for further analysis
- **Error Resilience**: Comprehensive error handling and user feedback

### 🌐 Language Support
- **Indonesian Focus**: Built-in slang dictionary with 200+ terms
- **Auto-Translation**: Indonesian to English for sentiment analysis
- **Language Detection**: Automatic language filtering when relevant

---

## 🛠 Installation

### Prerequisites

- **Python 3.8+**
- **Node.js 16+** (for tweet harvesting)
- **Discord Bot Token**
- **GROQ API Key** (free tier available)
- **Twitter Auth Token**

### Quick Setup

1. **Clone the Repository**
```bash
git clone https://github.com/yourusername/x-sentiment-analysis.git
cd x-sentiment-analysis
```

2. **Clone the Repository**
```bash
pip install -r requirements.txt
```

3. **Install Node.js Dependenciesy**
```bash
npm install -g tweet-harvest@2.6.1
```

4. **Configure Environment**
```bash
cp .env.example .env
```
Edit the .env file:
```bash
DISCORD_TOKEN=your_discord_bot_token_here
TWITTER_AUTH_TOKEN=your_twitter_auth_token_here  
GROQ_API_KEY=your_groq_api_key_here
DEFAULT_LIMIT=100
LOG_LEVEL=INFO
```

5. **Run the Bot**
```bash
python main.py bot
```

## 📖 Usage

### Basic Command
Use @XS followed by your search query:
```bash
@XS [your search query]
```
Example:
```bash
@XS sentimen masyarakat tentang pemilu 2024
@XS tweet dari jokowi bulan januari
@XS bagaimana opini twitter tentang startup teknologi
@XS analisis sentimen untuk pendidikan online
```
## 📊 Output Examples
### Sample Analysis Results
```bash
📊 Hasil Analisis Sentimen - Insights Detail

📈 Distribusi Sentimen:
✅ Positive: 45 tweets
❌ Negative: 30 tweets  
⚪ Neutral: 25 tweets

🎯 Sentimen Mayoritas: Positive

✅ Insight Positif:
• Kata kunci: startup, teknologi, inovasi, sukses, berkembang
• Engagement: 12.3 replies/tweet

❌ Insight Negatif:
• Kata kunci: masalah, error, bug, complaint, slow
• Engagement: 25.6 replies/tweet

⚪ Insight Netral:
• Kata kunci: update, informasi, berita, share, info
• Engagement: 8.2 replies/tweet
```

```bash
🔻 5 Tweet Negatif dengan Replies Terbanyak

📝 Tweet #1 (158 replies):
"Frustasi banget dengan layanan customer service yang slow response! 
Sudah 3 hari nunggu solusi tapi belum ada tindakan konkret. 
Very disappointed dengan pelayanan seperti ini."

❤️ Likes: 150 | 🔄 Retweets: 45
```

## 🏗 Project Structure
```bash
sentiment-analysis-x/
├── src/
│   ├── discord_bot.py
│   ├── smart_crawler.py
│   ├── groq_parser.py
│   ├── analyzer.py
│   ├── crawler.py
│   ├── preprocessor.py
│   ├── translator.py
│   ├── visualizer.py
│   └── config.py
├── tests/
│   ├── test_sentiment_analysis.py
├── results/
├── tweets-data/
├── main.py
├── requirements.txt
├── requirements-test.txt
└── .env
```

## ⚙️ Configuration
### Twitter Auth Token Setup
```bash
1. Visit Twitter and log in
2. Ctrl + Shift + I
3. Find application -> cookies -> auth_token
4. Use this as your TWITTER_AUTH_TOKEN
```
### GROQ API Setup
```bash
1. Sign up at GROQ
2. Get your free API key
3. Add to .env as GROQ_API_KEY
```
