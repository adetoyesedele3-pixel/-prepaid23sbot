# Prepaid23s Telegram Bot

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/)

A powerful multi-purpose Telegram bot with URL shortening, gift card conversion, AI image generation, word counter, and plagiarism checker.

## ✨ Features

- 🔗 **URL Shortener** - Shorten long links instantly
- 🎁 **Gift Card Converter** - Convert 15+ gift cards
- 🖼️ **AI Image Generator** - Create images from text
- 📝 **Word Counter** - Analyze text with statistics
- 🔍 **Plagiarism Checker** - Check content originality

## 🚀 Deploy on Railway

1. Fork this repository
2. Go to [Railway.app](https://railway.app)
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Add environment variable: `TELEGRAM_BOT_TOKEN`

## 🔧 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes | Your bot token from @BotFather |

## 📋 Commands

- `/start` - Show main menu
- `/help` - Get help
- `/about` - About the bot
- `/shorten URL` - Shorten a URL
- `/giftcard` - Check gift card rates
- `/convert AMOUNT CARD` - Convert gift card
- `/imagine prompt` - Generate AI image
- `/count text` - Count words
- `/plagiarism text` - Check plagiarism

## 📦 Dependencies

- python-telegram-bot==20.7
- Pillow==10.3.0

## 📞 Support

Contact: @prepaidsAdmin
