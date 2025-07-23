import os
import asyncio
import logging
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest

BOT_TOKEN = os.getenv('BOT_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
PORT = int(os.environ.get('PORT', 10000))

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

if not WEBHOOK_URL:
    print("[WARNING] WEBHOOK_URL environment variable is not set! Bot will not receive updates from Telegram.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 AI Chat Bot is Running - Visit https://t.me/your_bot to chat!"

@app.route('/webhook', methods=['POST'])
def webhook():
    logger.info(f"Webhook received: {request.get_json()}")
    if not request.is_json:
        return jsonify({"status": "error", "message": "Request must be JSON"}), 400
    try:
        update = Update.de_json(request.get_json(), application.bot)
        asyncio.run(application.process_update(update))
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.exception("Error processing webhook update:")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/health')
def health():
    return "ok", 200

# === Telegram Client Setup ===
client = TelegramClient('session_name', API_ID, API_HASH) if API_ID and API_HASH else None

# === AI Engine Configuration ===
ENGINE_CONFIG = {
    # ... (keep your existing engine config)
}

# === AI Query Handler ===
async def query_ai_engine(engine, prompt):
    # Dummy response for testing
    return f"Echo: {prompt}"

# === Telegram Handlers ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text(
            "🌟 Hello! I'm an advanced AI bot with collaborative AI engines.\n"
            "Send a message or project idea, and we'll work together to perfect it!"
        )
    except Exception as e:
        logger.exception("Error in /start handler:")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_message = update.message.text
        response = await query_ai_engine('openai', user_message)  # Default to OpenAI
        await update.message.reply_text(response)
    except Exception as e:
        logger.exception("Error in message handler:")
        await update.message.reply_text("Sorry, an error occurred while processing your message.")

# === Bot Initialization ===
def initialize_bot():
    global application
    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .updater(None)  # Disable polling since we're using webhooks
        .build()
    )
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return application

async def set_webhook():
    await application.bot.set_webhook(
        url=WEBHOOK_URL,
        drop_pending_updates=True
    )
    logger.info(f"Webhook set to: {WEBHOOK_URL}")
    logger.info(f"Bot username: @{(await application.bot.get_me()).username}")

# === Main Execution ===
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    # Initialize the bot
    initialize_bot()
    # Create a new event loop for the bot
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    # Set webhook
    if WEBHOOK_URL:
        loop.run_until_complete(set_webhook())
    else:
        logger.warning("WEBHOOK_URL is not set. Bot will not receive updates from Telegram!")
    # Run Flask app
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)