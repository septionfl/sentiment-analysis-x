# X Sentiment Analysis Bot

Discord bot untuk analisis sentimen tweet (Bahasa Indonesia) dengan crawling real-time dan laporan otomatis.

## 🚀 FEATURE
- Crawling Twitter (advanced search)
- Preprocessing & normalisasi teks (ID)
- Analisis sentimen (VADER)
- Export hasil CSV
- Notifikasi / laporan ke Discord (webhook / bot)

## 🛠️ REQUIREMENTS
- Python 3.8+
- Node.js 16+ (jika ada komponen frontend/integrasi Node)
- Discord Bot Token / Webhook URL
- Twitter Auth Token

## ⚙️ Setup (local)
1. Clone repo:
```bash
git clone https://github.com/septionfl/x-sentiment-analysis.git
cd x-sentiment-analysis
```

2. .env setup:
```bash
# Twitter Configuration
TWITTER_AUTH_TOKEN=your_twitter_auth_token_here

# Discord Configuration  
DISCORD_TOKEN=your_discord_bot_token_here
DISCORD_WEBHOOK_URL=your_discord_webhook_url_here

# Application Settings
DEFAULT_LIMIT=100
DEFAULT_FILENAME=hasil_crawling.csv
DEFAULT_SEARCH_QUERY=from:tanyakanrl lang:id until:2024-10-29 since:2024-10-01
LOG_LEVEL=INFO

```
