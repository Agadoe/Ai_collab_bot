import os
import asyncio
from dotenv import load_dotenv
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telethon import TelegramClient

# Load .env variables
load_dotenv()

# ENV Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", "10000"))

# Flask app setup
flask_app = Flask(__name__)

@flask_app.route("/", methods=["GET"])
def index():
    return "Bot is alive!"

@flask_app.route("/webhook", methods=["POST"])
def webhook():
    return "Webhook received", 200

# Telethon setup
telethon_client = TelegramClient("anon", API_ID, API_HASH)

# Telegram bot handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I'm your AI collab bot.")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(update.message.text)

# Telegram bot setup
async def run_telegram_bot():
    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    print(">> Bot started.")
    await application.initialize()
    await application.start()
    await application.bot.set_webhook(WEBHOOK_URL)
    print(f">> Webhook set to {WEBHOOK_URL}")
    await application.updater.start_polling()  # fallback polling if needed
    await application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL,
    )

# Run everything concurrently
async def main():
    print("📡 Flask server running on port", PORT)
    flask_task = asyncio.create_task(asyncio.to_thread(flask_app.run, host="0.0.0.0", port=PORT))
    bot_task = asyncio.create_task(run_telegram_bot())
    await asyncio.gather(flask_task, bot_task)

if __name__ == "__main__":
    asyncio.run(main())
