import os
import asyncio
import aiohttp
from flask import Flask, request, jsonify
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
import openai
import groq
import json

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

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

# === Flask Server Setup ===
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 AI Chat Bot is Running - Visit https://t.me/your_bot to chat!"

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "message": "Bot is running"}), 200

@app.route('/webhook', methods=['POST'])
def webhook():
    if not request.is_json:
        return jsonify({"status": "error", "message": "Request must be JSON"}), 400
    
    update = Update.de_json(request.get_json(), application.bot)
    asyncio.run_coroutine_threadsafe(
        application.process_update(update),
        application.update_queue._loop
    )
    return jsonify({"status": "success"}), 200

# === Telegram Client Setup ===
client = TelegramClient('session_name', API_ID, API_HASH) if API_ID and API_HASH else None

# === AI Engine Configuration ===
ENGINE_CONFIG = {
    'openai': {
        'api_key': OPENAI_API_KEY,
        'base_url': 'https://api.openai.com/v1',
        'model': 'gpt-4',
        'enabled': bool(OPENAI_API_KEY)
    },
    'groq': {
        'api_key': GROQ_API_KEY,
        'base_url': 'https://api.groq.com/openai/v1',
        'model': 'llama3-70b-8192',
        'enabled': bool(GROQ_API_KEY)
    },
    'openrouter': {
        'api_key': OPENROUTER_API_KEY,
        'base_url': 'https://openrouter.ai/api/v1',
        'model': 'anthropic/claude-3.5-sonnet',
        'enabled': bool(OPENROUTER_API_KEY)
    },
    'deepseek': {
        'api_key': DEEPSEEK_API_KEY,
        'base_url': 'https://api.deepseek.com/v1',
        'model': 'deepseek-chat',
        'enabled': bool(DEEPSEEK_API_KEY)
    },
    'xai': {
        'api_key': XAI_API_KEY,
        'base_url': 'https://api.x.ai/v1',
        'model': 'grok-beta',
        'enabled': bool(XAI_API_KEY)
    }
}

# === AI Query Handler ===
async def query_ai_engine(engine, prompt):
    """Query the specified AI engine with the given prompt."""
    if engine not in ENGINE_CONFIG:
        return "❌ Engine not found. Available engines: " + ", ".join(ENGINE_CONFIG.keys())
    
    config = ENGINE_CONFIG[engine]
    if not config['enabled']:
        return f"❌ {engine.upper()} is not configured. Please set the {engine.upper()}_API_KEY environment variable."
    
    try:
        client = openai.AsyncOpenAI(
            api_key=config['api_key'],
            base_url=config['base_url']
        )
        
        response = await client.chat.completions.create(
            model=config['model'],
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant. Provide clear, concise, and accurate responses."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"❌ Error querying {engine}: {str(e)}"

# === Telegram Handlers ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌟 Hello! I'm an advanced AI bot with collaborative AI engines.\n"
        "Send a message or project idea, and we'll work together to perfect it!\n\n"
        "Available commands:\n"
        "/start - Show this message\n"
        "/engines - List available AI engines\n"
        "/use <engine> - Switch to a specific AI engine"
    )

async def engines(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available AI engines and their status."""
    engine_list = []
    for engine, config in ENGINE_CONFIG.items():
        status = "✅ Enabled" if config['enabled'] else "❌ Disabled"
        engine_list.append(f"• {engine.upper()}: {status}")
    
    message = "🤖 Available AI Engines:\n\n" + "\n".join(engine_list)
    await update.message.reply_text(message)

async def use_engine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Switch to a specific AI engine."""
    if not context.args:
        await update.message.reply_text("Usage: /use <engine_name>\nExample: /use openai")
        return
    
    engine = context.args[0].lower()
    if engine not in ENGINE_CONFIG:
        await update.message.reply_text(f"❌ Engine '{engine}' not found. Use /engines to see available engines.")
        return
    
    if not ENGINE_CONFIG[engine]['enabled']:
        await update.message.reply_text(f"❌ {engine.upper()} is not configured.")
        return
    
    # Store the user's preferred engine
    context.user_data['preferred_engine'] = engine
    await update.message.reply_text(f"✅ Switched to {engine.upper()} engine!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages and route to AI engines."""
    user_message = update.message.text
    
    # Get user's preferred engine or default to first available
    preferred_engine = context.user_data.get('preferred_engine', 'openai')
    
    # If preferred engine is not available, find first available
    if not ENGINE_CONFIG[preferred_engine]['enabled']:
        for engine, config in ENGINE_CONFIG.items():
            if config['enabled']:
                preferred_engine = engine
                break
        else:
            await update.message.reply_text("❌ No AI engines are configured. Please set up at least one API key.")
            return
    
    # Send typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # Query the AI engine
    response = await query_ai_engine(preferred_engine, user_message)
    await update.message.reply_text(response)

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
    application.add_handler(CommandHandler('engines', engines))
    application.add_handler(CommandHandler('use', use_engine))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    return application

async def set_webhook():
    if WEBHOOK_URL:
        await application.bot.set_webhook(
            url=WEBHOOK_URL,
            drop_pending_updates=True
        )
        print(f"Webhook set at {WEBHOOK_URL}")
    else:
        print("Warning: WEBHOOK_URL not set. Webhook not configured.")

# === Main Execution ===
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    
    # Initialize the bot
    initialize_bot()
    
    # Create a new event loop for the bot
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Set webhook
    loop.run_until_complete(set_webhook())
    
    # Run Flask app
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)