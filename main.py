import os
import logging
from flask import Flask
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

BOT_TOKEN = os.getenv('BOT_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
PORT = int(os.environ.get('PORT', 10000))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app for health and home endpoints
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 AI Chat Bot is Running - Visit https://t.me/your_bot to chat!"

@app.route('/health')
def health():
    return "ok", 200

# Telegram Handlers

def get_application():
    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .build()
    )

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
            response = f"Echo: {user_message}"
            await update.message.reply_text(response)
        except Exception as e:
            logger.exception("Error in message handler:")
            await update.message.reply_text("Sorry, an error occurred while processing your message.")

    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return application

if __name__ == '__main__':
    # Start Flask in a background thread if you want health endpoints (optional)
    from threading import Thread
    Thread(target=lambda: app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)).start()

    # Start the Telegram bot webhook server (this will listen on the same port)
    application = get_application()
    logger.info(f"Setting webhook to: {WEBHOOK_URL}")
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL,
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )