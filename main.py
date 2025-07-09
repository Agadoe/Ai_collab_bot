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
        'url': "https://api.deepseek.com/v1/chat/completions",
        'model': "deepseek-chat",
        'temperature': 0.6,
        'max_tokens': 400,
        'system_message': "Respond accurately and provide technical support for collaborative efforts."
    },
    'grok': {
        'url': "https://api.x.ai/v1/chat/completions",
        'model': "grok-3",
        'temperature': 0.6,
        'max_tokens': 500,
        'system_message': "Act as a project coordinator, synthesizing inputs from all AIs for optimal results."
    }
}

# === AI Query Handler ===
async def query_ai_engine(engine, prompt):
    config = ENGINE_CONFIG[engine]
    api_key_var = f'{engine.upper()}_API_KEY'
    api_key = os.getenv(api_key_var)
    if not api_key:
        print(f"Missing {api_key_var} environment variable. Skipping {engine.upper()}.")
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    messages = [
        {"role": "system", "content": config['system_message']},
        {"role": "user", "content": prompt}
    ]

    json_data = {
        "model": config['model'],
        "messages": messages,
        "temperature": config['temperature'],
        'max_tokens': config['max_tokens']
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                config['url'],
                headers=headers,
                json=json_data,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status != 200:
                    print(f"{engine.upper()} API error: Status {resp.status}")
                    return None
                data = await resp.json()
                return data['choices'][0]['message']['content']
        except Exception as e:
            print(f"{engine.upper()} Error: {str(e)}")
            return None

# === Collaborative Project Manager ===
async def manage_collaborative_task(prompt):
    engines = ['openai', 'groq', 'openrouter', 'deepseek', 'grok']
    responses = {}

    for engine in engines:
        response = await query_ai_engine(engine, prompt)
        if response:
            responses[engine] = response
            print(f"{engine.upper()} collaborated: {response[:50]}...")

    if not responses:
        return "⚠️ No AI responses available for collaboration. Please try again."

    context = " ".join([f"{k}: {v}" for k, v in responses.items()])
    final_response = await query_ai_engine('grok', "Synthesize the following inputs into a perfect solution:" + context)
    if final_response:
        return final_response
    return f"⚠️ Synthesis failed, but here are raw inputs: {context[:200]}..."  # Fallback with partial context

# === Telegram Handlers ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌟 Hello! I'm an advanced AI bot with collaborative AI engines.\n"
        "Send a message or project idea, and we'll work together to perfect it!\n"
        "Use /scrape [chat_link] to scrape a Telegram chat."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    if "work together" in user_message.lower():
        response = await manage_collaborative_task(user_message)
    else:
        engines = ['openai', 'groq', 'openrouter', 'deepseek', 'grok']
        responses = {}
        for engine in engines:
            response = await query_ai_engine(engine, user_message)
            if response:
                responses[engine] = response
                print(f"{engine.upper()} responded: {response[:50]}...")  # Log first 50 chars
        if not responses:
            response = "⚠️ All systems busy. Please try again."
        else:
            response = responses[list(responses.keys())[0]]  # Use first successful response

    await update.message.reply_text(response)

async def scrape(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Please provide a chat link or username, e.g., /scrape https://t.me/example")
        return

    chat_input = context.args[0]
    try:
        await client.start(PHONE)
        target = await client.get_entity(chat_input)
        history = await client(GetHistoryRequest(
            peer=target,
            limit=100,  # Adjust limit as needed
            offset_date=None,
            offset_id=0,
            max_id=0,
            min_id=0,
            add_offset=0
        ))
        messages = [msg.message for msg in history.messages if hasattr(msg, 'message')]
        result = f"Scraped {len(messages)} messages from {chat_input}:\n" + "\n".join(messages[:10])  # Show first 10
        await update.message.reply_text(result)
    except Exception as e:
        await update.message.reply_text(f"Scraping failed: {str(e)}")
    finally:
        await client.disconnect()

# === Bot Setup ===
application = None  # Global to be used in webhook

async def telegram_bot():
    global application
    try:
        application = ApplicationBuilder().token(BOT_TOKEN).build()
        print(">> Application built successfully.")

        application.add_handler(CommandHandler('start', start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(CommandHandler('scrape', scrape))
        print(">> Handlers added successfully.")

        await application.initialize()
        print(">> Application initialized.")

        await application.start()
        print(">> Application started.")

        print(f">> Setting up webhook with URL: {WEBHOOK_URL}")
        response = await application.bot.set_webhook(url=WEBHOOK_URL)
        print(f">> Webhook set response: {response}")
        print(">> Webhook set. Bot is running...")

        await application.run_webhook(
            listen='0.0.0.0',
            port=port,
            url_path='/webhook',
            webhook_url=WEBHOOK_URL
        )
    except Exception as e:
        print(f"Telegram Bot Error: {str(e)}")
        if application:
            await application.stop()

# === Main Execution ===
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))  # Match Render's detected port
    print(f"📡 Flask server running on port {port}")

    app.run(host='0.0.0.0', port=port, use_reloader=False)