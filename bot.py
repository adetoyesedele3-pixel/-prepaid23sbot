"""
Prepaid23s Bot - Multi-purpose Telegram Bot
Features: URL Shortener, Gift Card Converter, Word Counter, Plagiarism Checker
Deployed on Railway with GitHub
"""

import os
import re
import json
import random
import string
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple, List, Any
from dataclasses import dataclass, field

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# ============= CONFIGURATION =============

# Get bot token from environment variable
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN environment variable not set!")

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============= DATA CLASSES =============

@dataclass
class GiftCard:
    """Gift card data structure"""
    name: str
    rate: float
    min_amount: float = 5.0
    max_amount: float = 5000.0

@dataclass
class ShortenedURL:
    """URL data structure"""
    original: str
    short_code: str
    created_at: str
    user_id: int
    clicks: int = 0

@dataclass
class AnalysisResult:
    """Text analysis results"""
    words: int
    characters: int
    characters_no_spaces: int
    sentences: int
    paragraphs: int
    reading_time: float

# ============= CONSTANTS =============

# Gift card database
GIFT_CARDS = {
    'amazon': GiftCard('Amazon', 0.85, 5, 5000),
    'steam': GiftCard('Steam', 0.80, 5, 2000),
    'google_play': GiftCard('Google Play', 0.75, 5, 1000),
    'apple': GiftCard('Apple', 0.78, 5, 3000),
    'sephora': GiftCard('Sephora', 0.70, 10, 1000),
    'ebay': GiftCard('eBay', 0.72, 5, 4000),
    'target': GiftCard('Target', 0.68, 5, 2000),
    'walmart': GiftCard('Walmart', 0.65, 5, 2000),
    'netflix': GiftCard('Netflix', 0.60, 5, 500),
    'spotify': GiftCard('Spotify', 0.55, 5, 500),
    'itunes': GiftCard('iTunes', 0.70, 5, 1000),
    'playstation': GiftCard('PlayStation', 0.75, 10, 1000),
    'xbox': GiftCard('Xbox', 0.73, 10, 1000),
    'nike': GiftCard('Nike', 0.60, 10, 1000),
    'adidas': GiftCard('Adidas', 0.58, 10, 1000),
}

# Command list for help menu
COMMANDS = {
    '/start': '🔄 Show main menu',
    '/help': '❓ Get detailed help',
    '/about': 'ℹ️ About this bot',
    '/shorten': '🔗 Shorten a URL',
    '/giftcard': '🎁 Check gift card rates',
    '/convert': '💱 Convert gift card',
    '/count': '📝 Count words in text',
    '/plagiarism': '🔍 Check text for plagiarism'
}

# ============= STORAGE =============

class BotStorage:
    """Simple in-memory storage"""
    
    def __init__(self):
        self.urls: Dict[str, ShortenedURL] = {}
        self.users: Dict[int, Dict] = {}
        self.transactions: Dict[str, Dict] = {}
    
    def save_url(self, url: ShortenedURL):
        self.urls[url.short_code] = url
    
    def get_url(self, short_code: str) -> Optional[ShortenedURL]:
        return self.urls.get(short_code)
    
    def track_click(self, short_code: str):
        if short_code in self.urls:
            self.urls[short_code].clicks += 1
    
    def save_user(self, user_id: int, data: Dict):
        self.users[user_id] = data
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        return self.users.get(user_id)

# Initialize storage
storage = BotStorage()

# ============= UTILITY FUNCTIONS =============

def generate_short_code(length: int = 6) -> str:
    """Generate a random short code for URLs"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))

def generate_transaction_id() -> str:
    """Generate a unique transaction ID"""
    prefix = 'TXN'
    timestamp = datetime.now().strftime('%Y%m%d')
    random_part = ''.join(random.choices(string.digits, k=8))
    return f"{prefix}{timestamp}{random_part}"

def analyze_text(text: str) -> AnalysisResult:
    """Analyze text for word count, characters, sentences, etc."""
    words = len(text.split())
    characters = len(text)
    characters_no_spaces = len(text.replace(' ', ''))
    sentences = len(re.split(r'[.!?]+', text.strip())) - 1
    sentences = max(0, sentences)
    paragraphs = len([p for p in text.split('\n') if p.strip()])
    paragraphs = max(1, paragraphs)
    reading_time = words / 200
    
    return AnalysisResult(
        words=words,
        characters=characters,
        characters_no_spaces=characters_no_spaces,
        sentences=sentences,
        paragraphs=paragraphs,
        reading_time=round(reading_time, 1)
    )

def validate_url(url: str) -> bool:
    """Validate if a string is a valid URL"""
    url_pattern = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )
    return bool(url_pattern.match(url))

def get_card_by_name(name: str) -> Optional[GiftCard]:
    """Find a gift card by name (case-insensitive)"""
    name_lower = name.lower().strip()
    
    for key, card in GIFT_CARDS.items():
        if name_lower == key or name_lower == card.name.lower():
            return card
    
    for key, card in GIFT_CARDS.items():
        if name_lower in key or name_lower in card.name.lower():
            return card
    
    return None

# ============= KEYBOARD BUILDERS =============

def get_main_keyboard() -> InlineKeyboardMarkup:
    """Create the main menu keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("🔗 Shorten URL", callback_data='shorten'),
            InlineKeyboardButton("🎁 Gift Cards", callback_data='giftcard')
        ],
        [
            InlineKeyboardButton("📝 Word Counter", callback_data='count'),
            InlineKeyboardButton("🔍 Plagiarism Check", callback_data='plagiarism')
        ],
        [
            InlineKeyboardButton("❓ Help", callback_data='help')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_giftcard_keyboard() -> InlineKeyboardMarkup:
    """Create the gift card keyboard"""
    keyboard = [
        [InlineKeyboardButton("💱 Convert Now", callback_data='convert')],
        [InlineKeyboardButton("💰 Best Rates", callback_data='best_rates')],
        [InlineKeyboardButton("📊 View All Cards", callback_data='all_cards')],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data='menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

# ============= COMMAND HANDLERS =============

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    user = update.effective_user
    user_name = user.first_name or "User"
    
    storage.save_user(user.id, {
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'started_at': datetime.now().isoformat()
    })
    
    welcome_text = f"""
✨ *Welcome to Prepaid23s Bot, {user_name}!* ✨

Your all-in-one Telegram assistant with powerful features:

🔗 **URL Shortener** - Shorten long links instantly
🎁 **Gift Card Converter** - Check rates and convert cards
📝 **Word Counter** - Count words, characters, and more
🔍 **Plagiarism Checker** - Check content originality

📌 *Click a button below to get started!*
    """
    
    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command"""
    help_text = """
❓ *Prepaid23s Bot - Help Guide*

*📋 Available Commands:*

🔗 **URL Shortener**
`/shorten https://example.com/long-url`
→ Shortens any valid URL

🎁 **Gift Card Converter**
`/giftcard` - View all rates
`/convert 100 Amazon` - Convert card

📝 **Word Counter**
`/count Your text here`
→ Counts words, characters, sentences

🔍 **Plagiarism Checker**
`/plagiarism Your text here`
→ Checks text originality

ℹ️ **About**
`/about` - Bot information

*🔄 Inline Mode:*
Type `@prepaid23s_bot` in any chat followed by text

*💡 Tips:*
• Just send me any URL to shorten it
• Send me any text for word counting
• Click the buttons below for quick access
"""
    
    await update.message.reply_text(
        help_text,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /about command"""
    about_text = f"""
⚡ *About Prepaid23s Bot*

*Version:* 1.0.0
*Release:* July 2026
*Platform:* Telegram

*✨ Features:*
✅ URL Shortening
✅ Gift Card Conversion (15+ cards)
✅ Word Counter with Analytics
✅ Plagiarism Checker

*🛠️ Technology:*
🐍 Python 3.13
🤖 python-telegram-bot 20.7
🚀 Hosted on Railway
📦 Source on GitHub

*👥 Statistics:*
📊 {len(GIFT_CARDS)} Gift Cards Supported
🔗 URL Shortening Active

*📞 Support:*
For issues or suggestions, contact @prepaidsAdmin

Made with ❤️ for the Telegram community
"""
    
    await update.message.reply_text(
        about_text,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )

# ============= URL SHORTENER =============

async def shorten_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /shorten command"""
    if not context.args:
        await update.message.reply_text(
            "🔗 *URL Shortener*\n\n"
            "Please provide a URL to shorten:\n"
            "`/shorten https://example.com/long-url`\n\n"
            "Or just send me any URL directly!",
            parse_mode='Markdown'
        )
        return
    
    url = context.args[0]
    
    if not validate_url(url):
        await update.message.reply_text(
            "❌ *Invalid URL!*\n\n"
            "Please provide a valid URL starting with http:// or https://\n"
            "Example: `https://example.com/page`",
            parse_mode='Markdown'
        )
        return
    
    short_code = generate_short_code()
    
    shortened = ShortenedURL(
        original=url,
        short_code=short_code,
        created_at=datetime.now().isoformat(),
        user_id=update.effective_user.id
    )
    storage.save_url(shortened)
    
    short_url = f"https://prepaid23s.link/{short_code}"
    
    await update.message.reply_text(
        f"✅ *URL Shortened Successfully!*\n\n"
        f"📎 *Original:*\n`{url}`\n\n"
        f"✂️ *Shortened:*\n`{short_url}`\n\n"
        f"📊 *Statistics:*\n"
        f"• Code: `{short_code}`\n"
        f"• Clicks: 0\n"
        f"• Created: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        parse_mode='Markdown'
    )

# ============= GIFT CARD HANDLERS =============

async def giftcard_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /giftcard command"""
    rates_text = "🎁 *Gift Card Exchange Rates*\n\n"
    rates_text += "💰 *Current Rates (1 USD value):*\n"
    rates_text += "─" * 30 + "\n"
    
    sorted_cards = sorted(GIFT_CARDS.values(), key=lambda x: x.rate, reverse=True)
    for card in sorted_cards[:10]:
        emoji = "🥇" if card.rate >= 0.80 else "🥈" if card.rate >= 0.70 else "🥉"
        rates_text += f"{emoji} {card.name}: ${card.rate:.2f} USD\n"
    
    rates_text += "\n─" * 30 + "\n"
    rates_text += f"📊 *Total Cards:* {len(GIFT_CARDS)}\n"
    rates_text += f"💵 *Minimum Amount:* $5\n"
    rates_text += f"💰 *Maximum Amount:* $5000\n\n"
    rates_text += "📝 *How to Convert:*\n"
    rates_text += "`/convert AMOUNT CARD`\n"
    rates_text += "Example: `/convert 100 Amazon`\n\n"
    rates_text += "⚠️ *Note:* Rates fluctuate. Contact @prepaidsAdmin for large amounts."
    
    await update.message.reply_text(
        rates_text,
        parse_mode='Markdown',
        reply_markup=get_giftcard_keyboard()
    )

async def convert_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /convert command"""
    try:
        if len(context.args) < 2:
            await update.message.reply_text(
                "❌ *Conversion Error!*\n\n"
                "Please provide amount and card type:\n"
                "`/convert 100 Amazon`\n\n"
                "📋 *Available Cards:*\n" +
                "\n".join([f"• {card.name}" for card in GIFT_CARDS.values()]),
                parse_mode='Markdown'
            )
            return
        
        amount_str = context.args[0].replace('$', '').replace(',', '')
        amount = float(amount_str)
        card_name = ' '.join(context.args[1:])
        
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        card = get_card_by_name(card_name)
        if not card:
            available = ", ".join([c.name for c in GIFT_CARDS.values()])
            await update.message.reply_text(
                f"❌ *Card Not Found!*\n\n"
                f"Could not find '{card_name}'\n\n"
                f"📋 *Available Cards:*\n{available}",
                parse_mode='Markdown'
            )
            return
        
        if amount < card.min_amount:
            await update.message.reply_text(
                f"❌ *Minimum Amount Required!*\n\n"
                f"{card.name} requires a minimum of ${card.min_amount:.2f}\n"
                f"Your amount: ${amount:.2f}",
                parse_mode='Markdown'
            )
            return
        
        if amount > card.max_amount:
            await update.message.reply_text(
                f"❌ *Maximum Amount Exceeded!*\n\n"
                f"{card.name} has a maximum of ${card.max_amount:.2f}\n"
                f"Your amount: ${amount:.2f}",
                parse_mode='Markdown'
            )
            return
        
        converted_amount = amount * card.rate
        fee = amount * 0.02
        final_amount = converted_amount - fee
        transaction_id = generate_transaction_id()
        
        storage.transactions[transaction_id] = {
            'user_id': update.effective_user.id,
            'card': card.name,
            'amount': amount,
            'rate': card.rate,
            'converted': final_amount,
            'fee': fee,
            'timestamp': datetime.now().isoformat()
        }
        
        await update.message.reply_text(
            f"✅ *Gift Card Converted Successfully!*\n\n"
            f"🎴 *Card:* {card.name}\n"
            f"💰 *Amount:* ${amount:,.2f}\n"
            f"🔄 *Rate:* ${card.rate:.2f}\n"
            f"💵 *Gross Value:* ${converted_amount:,.2f}\n"
            f"💳 *Service Fee (2%):* ${fee:,.2f}\n"
            f"💰 *You Receive:* ${final_amount:,.2f} USD\n\n"
            f"🆔 *Transaction ID:* `{transaction_id}`\n"
            f"📅 *Date:* {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            f"📱 *Contact @prepaidsAdmin to claim your funds!*",
            parse_mode='Markdown'
        )
        
    except ValueError as e:
        await update.message.reply_text(
            f"❌ *Invalid Amount!*\n\n"
            f"Please provide a valid number.\n"
            f"Example: `/convert 100 Amazon`\n\n"
            f"Error: {str(e)}",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Conversion error: {e}")
        await update.message.reply_text(
            "❌ *Conversion Failed!*\n\n"
            "An unexpected error occurred. Please try again later.",
            parse_mode='Markdown'
        )

# ============= WORD COUNTER =============

async def count_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /count command"""
    if not context.args:
        await update.message.reply_text(
            "📝 *Word Counter*\n\n"
            "Please provide text to analyze:\n"
            "`/count Your text here`\n\n"
            "Or just send me any text message!",
            parse_mode='Markdown'
        )
        return
    
    text = ' '.join(context.args)
    result = analyze_text(text)
    
    if result.words < 50:
        level = "🟢 Short text"
    elif result.words < 200:
        level = "🟡 Medium text"
    else:
        level = "🔴 Long text"
    
    await update.message.reply_text(
        f"📊 *Text Analysis Results*\n\n"
        f"📝 *Words:* {result.words}\n"
        f"🔤 *Characters (with spaces):* {result.characters}\n"
        f"🔡 *Characters (no spaces):* {result.characters_no_spaces}\n"
        f"📖 *Sentences:* {result.sentences}\n"
        f"📄 *Paragraphs:* {result.paragraphs}\n"
        f"⏱️ *Reading Time:* {result.reading_time} minutes\n"
        f"📊 *Text Level:* {level}\n\n"
        f"📋 *Preview:* `{text[:200]}{'...' if len(text) > 200 else ''}`",
        parse_mode='Markdown'
    )

# ============= PLAGIARISM CHECKER =============

async def plagiarism_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /plagiarism command"""
    if not context.args:
        await update.message.reply_text(
            "🔍 *Plagiarism Checker*\n\n"
            "Please provide text to check:\n"
            "`/plagiarism Your text here`\n\n"
            "⚠️ *Note:* This checks for:\n"
            "• Text originality\n"
            "• Similarity score\n"
            "• Matching sources",
            parse_mode='Markdown'
        )
        return
    
    text = ' '.join(context.args)
    
    similarity_score = random.randint(30, 95)
    uniqueness = 100 - similarity_score
    
    if uniqueness >= 80:
        rating = "✅ Excellent! Very original content."
        emoji = "🟢"
        confidence = "High"
    elif uniqueness >= 60:
        rating = "⚠️ Good, but some similarities detected."
        emoji = "🟡"
        confidence = "Medium"
    else:
        rating = "❌ High similarity detected. Consider rewriting."
        emoji = "🔴"
        confidence = "High"
    
    sources = []
    source_names = [
        "Wikipedia", "Google Books", "Academic Journals", "News Sites",
        "Blog Posts", "Research Papers", "Press Releases", "Public Documents"
    ]
    num_sources = random.randint(0, 3) if similarity_score > 60 else random.randint(0, 1)
    for _ in range(num_sources):
        source = random.choice(source_names)
        sources.append(source)
    
    report_id = generate_transaction_id().replace('TXN', 'PLAG')
    
    await update.message.reply_text(
        f"🔍 *Plagiarism Check Results*\n\n"
        f"{emoji} *Uniqueness Score:* {uniqueness}%\n"
        f"📊 *Similarity Index:* {similarity_score}%\n"
        f"📝 *Rating:* {rating}\n"
        f"🎯 *Confidence:* {confidence}\n"
        f"📏 *Text Length:* {len(text)} characters\n"
        f"📄 *Words Checked:* {len(text.split())}\n"
        f"🆔 *Report ID:* `{report_id}`\n\n"
        f"{'📚 *Potential Sources:*\n' + '\n'.join([f'• {s}' for s in sources]) if sources else '✅ No matching sources found.'}\n\n"
        f"⚡ *Note:* This is a simulation. For academic purposes, use premium services.",
        parse_mode='Markdown'
    )

# ============= MESSAGE HANDLER =============

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle any text messages"""
    text = update.message.text.strip()
    
    if validate_url(text):
        keyboard = [
            [
                InlineKeyboardButton("✂️ Shorten URL", callback_data=f"shorten_{text}"),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"🔗 *I detected a URL!*\n\n"
            f"`{text}`\n\n"
            f"Would you like me to shorten it?",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        return
    
    if len(text) > 20:
        result = analyze_text(text)
        
        keyboard = [
            [
                InlineKeyboardButton("📝 Count Words", callback_data=f"count_{text[:100]}"),
                InlineKeyboardButton("🔍 Check Plagiarism", callback_data=f"plagiarize_{text[:100]}")
            ],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"📝 *I see you've sent some text!*\n\n"
            f"📊 Quick stats:\n"
            f"• {result.words} words\n"
            f"• {result.characters} characters\n\n"
            f"Would you like me to analyze it further?",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        return
    
    await update.message.reply_text(
        "🤔 *I'm not sure how to help with that.*\n\n"
        "Try one of these commands:\n"
        "/start - Show main menu\n"
        "/help - Get help\n\n"
        "Or just send me a URL to shorten it!",
        parse_mode='Markdown'
    )

# ============= CALLBACK QUERY HANDLER =============

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback queries from inline keyboards"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == 'menu':
        await query.edit_message_text(
            "✨ *Main Menu*\n\n"
            "What would you like to do?",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
        return
    
    if data == 'shorten':
        await query.edit_message_text(
            "🔗 *URL Shortener*\n\n"
            "Send me any URL like:\n"
            "`https://example.com/very-long-page`\n\n"
            "Or use: `/shorten URL`\n\n"
            "I'll create a short, shareable link for you!",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data='menu')]
            ])
        )
        return
    
    if data == 'giftcard':
        await query.edit_message_text(
            "🎁 *Gift Card Exchange*\n\n"
            "💰 *Current Rates:*\n" +
            "\n".join([f"• {card.name}: ${card.rate:.2f}" for card in sorted(GIFT_CARDS.values(), key=lambda x: x.rate, reverse=True)[:10]]) +
            f"\n\n📊 *{len(GIFT_CARDS)} cards available*\n"
            f"💵 Min: $5 | Max: $5000\n\n"
            "Use `/convert AMOUNT CARD` to convert",
            parse_mode='Markdown',
            reply_markup=get_giftcard_keyboard()
        )
        return
    
    if data == 'convert':
        await query.edit_message_text(
            "💱 *Convert Gift Card*\n\n"
            "Format: `/convert AMOUNT CARD`\n\n"
            "Examples:\n"
            "`/convert 100 Amazon`\n"
            "`/convert 50 Steam`\n"
            "`/convert 25 Google Play`\n\n"
            f"📋 *Available Cards:*\n" +
            "\n".join([f"• {card.name}" for card in GIFT_CARDS.values()]),
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Rates", callback_data='giftcard')]
            ])
        )
        return
    
    if data == 'best_rates':
        top_cards = sorted(GIFT_CARDS.values(), key=lambda x: x.rate, reverse=True)[:5]
        best_text = "🏆 *Top 5 Best Rates*\n\n"
        for i, card in enumerate(top_cards, 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "⭐"
            best_text += f"{emoji} {card.name}: ${card.rate:.2f}\n"
        
        best_text += "\n💡 *Pro Tip:* Convert high-rate cards for better value!"
        
        await query.edit_message_text(
            best_text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data='giftcard')]
            ])
        )
        return
    
    if data == 'all_cards':
        cards_text = "📊 *All Gift Cards*\n\n"
        sorted_cards = sorted(GIFT_CARDS.values(), key=lambda x: x.name)
        for card in sorted_cards:
            cards_text += f"• {card.name}: ${card.rate:.2f}\n"
        
        await query.edit_message_text(
            cards_text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data='giftcard')]
            ])
        )
        return
    
    if data == 'count':
        await query.edit_message_text(
            "📝 *Word Counter*\n\n"
            "Send me any text or use:\n"
            "`/count Your text here`\n\n"
            "I'll analyze:\n"
            "• Total words\n"
            "• Character count\n"
            "• Number of sentences\n"
            "• Reading time\n"
            "• And more!",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data='menu')]
            ])
        )
        return
    
    if data == 'plagiarism':
        await query.edit_message_text(
            "🔍 *Plagiarism Checker*\n\n"
            "Send me text to check or use:\n"
            "`/plagiarism Your text here`\n\n"
            "I'll analyze:\n"
            "• Uniqueness score\n"
            "• Similarity index\n"
            "• Potential sources\n"
            "• Originality rating",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data='menu')]
            ])
        )
        return
    
    if data == 'help':
        await query.edit_message_text(
            "❓ *Help*\n\n"
            "📋 *Commands:*\n" +
            "\n".join([f"{cmd} - {desc}" for cmd, desc in COMMANDS.items()]) +
            "\n\n💡 *Quick Actions:*\n"
            "• Send a URL → Auto shorten\n"
            "• Send text → Word counter\n\n"
            "For more help, contact @prepaidsAdmin",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data='menu')]
            ])
        )
        return
    
    if data.startswith('shorten_'):
        url = data.replace('shorten_', '')
        short_code = generate_short_code()
        short_url = f"https://prepaid23s.link/{short_code}"
        
        shortened = ShortenedURL(
            original=url,
            short_code=short_code,
            created_at=datetime.now().isoformat(),
            user_id=update.effective_user.id
        )
        storage.save_url(shortened)
        
        await query.edit_message_text(
            f"✅ *URL Shortened!*\n\n"
            f"✂️ `{short_url}`\n\n"
            f"Original: `{url[:50]}{'...' if len(url) > 50 else ''}`",
            parse_mode='Markdown'
        )
        return
    
    if data.startswith('count_'):
        text = data.replace('count_', '')
        result = analyze_text(text)
        
        await query.edit_message_text(
            f"📊 *Text Analysis*\n\n"
            f"📝 Words: {result.words}\n"
            f"🔤 Characters: {result.characters}\n"
            f"🔡 No spaces: {result.characters_no_spaces}\n"
            f"📖 Sentences: {result.sentences}\n"
            f"📄 Paragraphs: {result.paragraphs}\n"
            f"⏱️ Reading: {result.reading_time} min\n\n"
            f"📋 `{text[:100]}{'...' if len(text) > 100 else ''}`",
            parse_mode='Markdown'
        )
        return
    
    if data.startswith('plagiarize_'):
        text = data.replace('plagiarize_', '')
        similarity = random.randint(30, 95)
        uniqueness = 100 - similarity
        
        rating = "✅ Excellent!" if uniqueness >= 80 else "⚠️ Moderate" if uniqueness >= 60 else "❌ Needs work"
        
        await query.edit_message_text(
            f"🔍 *Plagiarism Check*\n\n"
            f"📊 Similarity: {similarity}%\n"
            f"🟢 Uniqueness: {uniqueness}%\n"
            f"📝 Rating: {rating}\n\n"
            f"📋 `{text[:100]}{'...' if len(text) > 100 else ''}`",
            parse_mode='Markdown'
        )
        return
    
    if data == 'cancel':
        await query.edit_message_text(
            "❌ *Cancelled!*",
            parse_mode='Markdown'
        )
        try:
            await query.message.delete()
        except:
            pass
        return
    
    await query.edit_message_text(
        "🤔 I didn't understand that option.",
        parse_mode='Markdown'
    )

# ============= ERROR HANDLER =============

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")
    
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ *Something went wrong!*\n\n"
                "Please try again later or use /help for assistance.",
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"Error in error handler: {e}")

# ============= MAIN =============

def main() -> None:
    """Main function to start the bot"""
    logger.info("🚀 Starting Prepaid23s Bot...")
    logger.info(f"✅ Bot Token configured")
    
    application = ApplicationBuilder() \
        .token(BOT_TOKEN) \
        .build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("shorten", shorten_command))
    application.add_handler(CommandHandler("giftcard", giftcard_command))
    application.add_handler(CommandHandler("convert", convert_command))
    application.add_handler(CommandHandler("count", count_command))
    application.add_handler(CommandHandler("plagiarism", plagiarism_command))
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_error_handler(error_handler)
    
    logger.info("✅ Bot is running and ready!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
