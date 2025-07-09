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
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
PHONE = os.getenv('PHONE')

if not all([OPENAI_API_KEY, GROQ_API_KEY, OPENROUTER_API_KEY, DEEPSEEK_API_KEY, XAI_API_KEY, BOT_TOKEN, WEBHOOK_URL, API_ID, API_HASH, PHONE]):
    raise ValueError("Missing one or more required environment variables.")

# === Flask Server Setup ===
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 AI Chat Bot is Running - Visit https://t.me/your_bot to chat!"

@app.route('/webhook', methods=['POST'])
async def webhook():
    data = request.get_json()
    if not data:
        return '', 400
    update = Update.de_json(data, application.bot)
    await application.update_queue.put(update)
    return '', 200

# === Telegram Client Setup ===
client = TelegramClient('session_name', API_ID, API_HASH)

# === AI Engine Configuration ===
ENGINE_CONFIG = {
    # ... (keep your existing engine config)
}

# === AI Query Handler ===
async def query_ai_engine(engine, prompt):
    # ... (keep your existing query_ai_engine function)
    pass

# === Collaborative Project Manager ===
async def manage_collaborative_task(prompt):
    # ... (keep your existing manage_collaborative_task function)
    pass

# === Telegram Handlers ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (keep your existing start function)
    pass

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (keep your existing handle_message function)
    pass

async def scrape(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (keep your existing scrape function)
    pass

# === Bot Setup ===
application = None

async def setup_bot():
    global application
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CommandHandler('scrape', scrape))
    
    await application.initialize()
    await application.start()
    
    # Set webhook
    await application.bot.set_webhook(url=WEBHOOK_URL)
    print(f"Bot is running with webhook at {WEBHOOK_URL}")

async def shutdown_bot():
    if application:
        await application.stop()
        await application.shutdown()

def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(setup_bot())
    except KeyboardInterrupt:
        loop.run_until_complete(shutdown_bot())
    finally:
        loop.close()

# === Main Execution ===
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    
    # Run Flask in a separate thread
    from threading import Thread
    flask_thread = Thread(target=lambda: app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False))
    flask_thread.start()
    
    # Run the bot in the main thread
    run_bot()