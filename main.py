import os
import asyncio
import aiohttp
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters
)
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest

# === Environment Variables ===
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
XAI_API_KEY = os.getenv('XAI_API_KEY')
BOT_TOKEN = os.getenv('BOT_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')  # e.g., https://ai-collab-bot.onrender.com
API_ID = os.getenv('API_ID')  # Telegram API ID from my.telegram.org
API_HASH = os.getenv('API_HASH')  # Telegram API Hash from my.telegram.org
PHONE = os.getenv('PHONE')  # Your phone number with country code, e.g., +1234567890

if not all([OPENAI_API_KEY, GROQ_API_KEY, OPENROUTER_API_KEY, DEEPSEEK_API_KEY, XAI_API_KEY, BOT_TOKEN, WEBHOOK_URL, API_ID, API_HASH, PHONE]):
    raise ValueError("Missing one or more required environment variables. Check Render environment settings.")

# === Flask Server Setup ===
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 AI Chat Bot is Running - Visit https://t.me/your_bot to chat!"

@app.route('/webhook', methods=['POST'])
async def webhook():
    update = Update.de_json(await request.get_json(), application.bot)
    await application.process_update(update)
    return '', 200

# === Telegram Client Setup ===
client = TelegramClient('session_name', API_ID, API_HASH)

# === AI Engine Configuration ===
ENGINE_CONFIG = {
    'openai': {
        'url': "https://api.openai.com/v1/chat/completions",
        'model': "gpt-4-turbo",
        'temperature': 0.7,
        'max_tokens': 400,
        'system_message': "You're a helpful assistant. Contribute to collaborative tasks with concise insights."
    },
    'groq': {
        'url': "https://api.groq.com/openai/v1/chat/completions",
        'model': "llama3-70b-8192",
        'temperature': 0.5,
        'max_tokens': 500,
        'system_message': "Provide detailed and thoughtful contributions to collaborative projects."
    },
    'openrouter': {
        'url': "https://openrouter.ai/api/v1/chat/completions",
        'model': "google/palm-2",
        'temperature': 0.6,
        'max_tokens': 450,
        'system_message': "Be engaging and offer creative input for collaborative tasks."
    },
    'deepseek': {
        'url': "https://api.deepseek.com/v1/chat/completions",  # Direct API endpoint
        'model': "deepseek-chat",
        'temperature': 0.6,
        'max_tokens': 400,
        'system_message': "Respond accurately and provide technical support for collaborative efforts."
    },
    'grok': {
        'url': "https://api.x.ai/v1/chat/completions",  # Direct API endpoint
        'model': "grok-3",
        'temperature': 0.6,
        'max_tokens': 500,
        'system_message': "Act as a project coordinator, synthesizing inputs from all AIs for optimal results."
    }
}

# === AI Query Handler ===
async def query_ai_engine(engine, prompt):