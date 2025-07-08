import os
import threading
import asyncio
import nest_asyncio
import aiohttp
from flask import Flask
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters
)
from discord.ext import commands
from discord import Intents
from nio import AsyncClient, RoomMessageText

# === Environment Variables ===
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
BOT_TOKEN = os.getenv('BOT_TOKEN')
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
MATRIX_ACCESS_TOKEN = os.getenv('MATRIX_ACCESS_TOKEN')
MATRIX_HOMESERVER = os.getenv('MATRIX_HOMESERVER', 'https://matrix.org')
XAI_API_KEY = os.getenv('XAI_API_KEY')

if not all([OPENAI_API_KEY, GROQ_API_KEY, OPENROUTER_API_KEY, DEEPSEEK_API_KEY, BOT_TOKEN, XAI_API_KEY]):
    raise ValueError("Missing one or more required environment variables.")

# === Flask Server Setup ===
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 AI Chat Bot is Running - Visit https://t.me/your_bot, Discord, or Matrix to chat!"

# === Conversation Memory ===
class ConversationMemory:
    def __init__(self, max_history=5):
        self.history = {}
        self.max_history = max_history

    def add_message(self, user_id, role, content):
        if user_id not in self.history:
            self.history[user_id] = []
        self.history[user_id].append({"role": role, "content": content})
        self.history[user_id] = self.history[user_id][-self.max_history:]

conversation_memory = ConversationMemory()

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
async def query_ai_engine(engine, user_id, prompt, context=None):
    config = ENGINE_CONFIG[engine]
    api_key = globals()[f'{engine.upper()}_API_KEY']

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    messages = [
        {"role": "system", "content": config['system_message']},
        *conversation_memory.history.get(user_id, []),
        {"role": "user", "content": prompt}
    ]
    if context:
        messages.append({"role": "assistant", "content": f"Context from other AIs: {context}"})

    json_data = {
        "model": config['model'],
        "messages": messages,
        "temperature": config['temperature'],
        "max_tokens": config['max_tokens']
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
                    return None
                data = await resp.json()
                return data['choices'][0]['message']['content']
        except Exception as e:
            print(f"{engine.upper()} Error: {str(e)}")
            return None

# === Collaborative Project Manager ===
async def manage_collaborative_task(user_id, prompt):
    engines = ['openai', 'groq', 'openrouter', 'deepseek', 'grok']
    responses = {}

    for engine in engines:
        response = await query_ai_engine(engine, user_id, prompt)
        if response:
            responses[engine] = response

    context = " ".join([f"{k}: {v}" for k, v in responses.items()])
    final_response = await query_ai_engine('grok', user_id, "Synthesize the following inputs into a perfect solution:", context)
    if final_response:
        conversation_memory.add_message(user_id, "assistant", final_response)
        return final_response
    return "⚠️ Collaboration failed. Please try again."

# === Telegram Handlers ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌟 Hello! I'm an advanced AI bot with collaborative AI engines.\n"
        "Send a message or project idea, and we'll work together to perfect it!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_message = update.message.text

    conversation_memory.add_message(user_id, "user", user_message)

    if "work together" in user_message.lower():
        response = await manage_collaborative_task(user_id, user_message)
    else:
        engines = ['openai', 'groq', 'openrouter', 'deepseek', 'grok']
        response = None
        for engine in engines:
            response = await query_ai_engine(engine, user_id, user_message)
            if response:
                conversation_memory.add_message(user_id, "assistant", response)
                break
        if not response:
            response = "⚠️ All systems busy. Please try again."

    await update.message.reply_text(response)

async def telegram_bot():
    try:
        application = ApplicationBuilder().token(BOT_TOKEN).build()

        application.add_handler(CommandHandler('start', start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        await application.initialize()
        await application.start()
        print(">> Telegram bot started polling...")
        await application.updater.start_polling()
        await application.updater.idle()
    except Exception as e:
        print(f"Telegram Bot Error: {str(e)}")

# === Discord Bot Setup ===
intents = Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'>> Discord bot {bot.user} has connected!')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    user_id = message.author.id
    prompt = message.content
    conversation_memory.add_message(user_id, "user", prompt)

    if "work together" in prompt.lower():
        response = await manage_collaborative_task(user_id, prompt)
    else:
        engines = ['openai', 'groq', 'openrouter', 'deepseek', 'grok']
        response = None
        for engine in engines:
            response = await query_ai_engine(engine, user_id, prompt)
            if response:
                conversation_memory.add_message(user_id, "assistant", response)
                break
        if not response:
            response = "⚠️ All systems busy. Please try again."

    await message.channel.send(response)

# === Matrix Handler ===
async def matrix_handler():
    if not MATRIX_ACCESS_TOKEN:
        print("Matrix token not set. Skipping...")
        return
    client = AsyncClient(MATRIX_HOMESERVER, "your-bot-user")  # Replace with your bot user ID
    client.access_token = MATRIX_ACCESS_TOKEN
    client.next_batch = None

    async def message_callback(room, event):
        user_id = event.sender
        prompt = event.body
        if user_id and prompt and not event.sender.startswith("@your-bot-user"):  # Avoid self-response
            conversation_memory.add_message(user_id, "user", prompt)

            if "work together" in prompt.lower():
                response = await manage_collaborative_task(user_id, prompt)
            else:
                engines = ['openai', 'groq', 'openrouter', 'deepseek', 'grok']
                response = None
                for engine in engines:
                    response = await query_ai_engine(engine, user_id, prompt)
                    if response:
                        conversation_memory.add_message(user_id, "assistant", response)
                        break
                if not response:
                    response = "⚠️ All systems busy. Please try again."

            await client.room_send(
                room.room_id,
                message_type="m.room.message",
                content={"msgtype": "m.text", "body": response}
            )

    client.add_event_callback(message_callback, RoomMessageText)
    await client.sync_forever(timeout=30000)

# === Main Execution ===
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    flask_thread = threading.Thread(
        target=lambda: app.run(host='0.0.0.0', port=port, use_reloader=False),
        daemon=True
    )
    flask_thread.start()
    print(f"📡 Flask server running on port {port}")

    nest_asyncio.apply()
    loop = asyncio.get_event_loop()

    if DISCORD_BOT_TOKEN:
        loop.create_task(bot.start(DISCORD_BOT_TOKEN))

    if MATRIX_ACCESS_TOKEN:
        loop.create_task(matrix_handler())

    try:
        print("🤖 Starting AI chatbot...")
        loop.create_task(telegram_bot())
        loop.run_forever()
    except KeyboardInterrupt:
        print("\n🔴 Shutting down...")
        if DISCORD_BOT_TOKEN:
            loop.create_task(bot.close())
        loop.close()