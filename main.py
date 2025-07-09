import os
import logging
import asyncio
import threading
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://your-app.onrender.com/webhook")

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

app = Flask(__name__)
application = None  # Will hold the telegram application instance

# Example command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! Bot is up and running.")

# Main Telegram bot setup
async def telegram_bot():
    global application
    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .build()
    )

    # Add handlers
    application.add_handler(CommandHandler("start", start))

    print(">> Handlers added successfully.")
    print(">> Bot started.")
    await application.initialize()

    # Set webhook
    await application.bot.set_webhook(WEBHOOK_URL)
    print(f">> Webhook set to {WEBHOOK_URL}")

    # Start webhook mode
    await application.start()
    await application.updater.start_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        url_path="/webhook",
        webhook_url=WEBHOOK_URL
    )

# Flask webhook route
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == "POST":
        data = request.get_json(force=True)
        update = Update.de_json(data, application.bot)
        asyncio.create_task(application.process_update(update))
    return "OK"

# Flask server route
@app.route('/')
def index():
    return "✅ Flask server is up!"

# Run both Flask and bot
if __name__ == '__main__':
    def start_bot():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(telegram_bot())

    threading.Thread(target=start_bot).start()
    print("📡 Flask server running on port 10000")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
