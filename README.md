# Prepaid23s Telegram Bot

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/YOUR_TEMPLATE)

A powerful multi-purpose Telegram bot with URL shortening, gift card conversion, AI image generation, word counter, and plagiarism checker.

## ✨ Features

- 🔗 **URL Shortener** - Shorten long links instantly
- 🎁 **Gift Card Converter** - Convert 15+ gift cards
- 🖼️ **AI Image Generator** - Create images from text
- 📝 **Word Counter** - Analyze text with statistics
- 🔍 **Plagiarism Checker** - Check content originality

## 🚀 Quick Deploy

### Option 1: Deploy on Railway (Recommended)

1. Click the "Deploy on Railway" button above
2. Add environment variable: `TELEGRAM_BOT_TOKEN`
3. Done!

### Option 2: Manual Deployment

```bash
# Clone repository
git clone https://github.com/yourusername/prepaid23s-bot
cd prepaid23s-bot

# Install dependencies
pip install -r requirements.txt

# Set environment variable
export TELEGRAM_BOT_TOKEN="your_bot_token"

# Run bot
python bot.py
