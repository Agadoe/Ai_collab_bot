import os
import threading
import asyncio
import aiohttp
import json
import io
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters
)
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# === Environment Variables ===
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
BOT_TOKEN = os.getenv('BOT_TOKEN')
XAI_API_KEY = os.getenv('XAI_API_KEY')
GOOGLE_CREDENTIALS = os.getenv('GOOGLE_CREDENTIALS')
GOOGLE_DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')  # e.g., https://ai-collab-bot.onrender.com

if not all([OPENAI_API_KEY, GROQ_API_KEY, OPENROUTER_API_KEY, DEEPSEEK_API_KEY, BOT_TOKEN, XAI_API_KEY, GOOGLE_CREDENTIALS, GOOGLE_DRIVE_FOLDER_ID, WEBHOOK_URL]):
    raise ValueError("Missing one or more required environment variables. Check Render environment settings.")

try:
    credentials_dict = json.loads(os.environ['GOOGLE_CREDENTIALS'])
    credentials = Credentials.from_service_account_info(credentials_dict)
    drive_service = build('drive', 'v3', credentials=credentials)
except json.JSONDecodeError as e:
    print(f"Invalid GOOGLE_CREDENTIALS format: {str(e)}. Falling back to in-memory storage.")
    drive_service = None
except Exception as e:
    print(f"Google Drive setup error: {str(e)}. Falling back to in-memory storage.")
    drive_service = None

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

# === Conversation Memory with Google Drive Fallback ===
class ConversationMemory:
    def __init__(self, max_history=5):
        self.history = {}
        self.max_history = max_history
        if drive_service:
            self._load_from_drive()

    def _load_from_drive(self):
        try:
            query = f"'{GOOGLE_DRIVE_FOLDER_ID}' in parents"
            results = drive_service.files().list(q=query, fields="files(id, name)").execute()
            for file in results.get('files', []):
                if file['name'].startswith('chat_history_'):
                    file_id = file['id']
                    request = drive_service.files().get_media(fileId=file_id)
                    fh = request.execute()
                    user_id = file['name'].replace('chat_history_', '').replace('.json', '')
                    self.history[user_id] = json.loads(fh)
        except Exception as e:
            print(f"Error loading from Drive: {str(e)}")

    def _save_to_drive(self, user_id):
        if not drive_service:
            return
        history_data = self.history.get(user_id, [])
        file_metadata = {
            'name': f'chat_history_{user_id}.json',
            'parents': [GOOGLE_DRIVE_FOLDER_ID]
        }
        media = MediaFileUpload(
            io.BytesIO(json.dumps(history_data).encode()),
            mimetype='application/json',
            resumable=True
        )
        try:
            query = f"name='chat_history_{user_id}.json' and '{GOOGLE_DRIVE_FOLDER_ID}' in parents"
            results = drive_service.files().list(q=query, fields="files(id)").execute()
            if results.get('files', []):
                file_id = results['files'][0]['id']
                drive_service.files().update(fileId=file_id, media_body=media).execute()
            else:
                drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        except Exception as e:
            print(f"Error saving to Drive: {str(e)}")

    def add_message(self, user_id, role, content):
        if user_id not in self.history:
            self.history[user_id] = []
        self.history[user_id].append({"role": role, "content": content})
        self.history[user_id] = self.history[user_id][-self.max_history:]
        self._save_to_drive(user_id)

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
                    print(f"{engine.upper()} API error: Status {resp.status}")
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
            print(f"{engine.upper()} collaborated: {response[:50]}...")

    if not responses:
        return "⚠️ No AI responses available for collaboration. Please try again."

    context = " ".join([f"{k}: {v}" for k, v in responses.items()])
    final_response = await query_ai_engine('grok', user_id, "Synthesize the following inputs into a perfect solution:", context)
    if final_response:
        conversation_memory.add_message(user_id, "assistant", final_response)
        return final_response
    return f"⚠️ Synthesis failed, but here are raw inputs: {context[:200]}..."  # Fallback with partial context

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
        responses = {}
        for engine in engines:
            response = await query_ai_engine(engine, user_id, user_message)
            if response:
                responses[engine] = response
                conversation_memory.add_message(user_id, "assistant", response)
                print(f"{engine.upper()} responded: {response[:50]}...")  # Log first 50 chars
        if not responses:
            response = "⚠️ All systems busy. Please try again."
        else:
            response = responses[list(responses.keys())[0]]  # Use first successful response

    await update.message.reply_text(response)

# === Bot Setup ===
application = None  # Global to be used in webhook

async def telegram_bot():
    global application
    try:
        application = ApplicationBuilder().token(BOT_TOKEN).build()
        print(">> Application built successfully.")

        application.add_handler(CommandHandler('start', start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        print(">> Handlers added successfully.")

        await application.initialize()
        print(">> Application initialized.")

        await application.start()
        print(">> Application started.")

        print(f">> Setting up webhook with URL: {WEBHOOK_URL}")
        response = await application.bot.set_webhook(url=WEBHOOK_URL)
        print(f">> Webhook set response: {response}")
        print(">> Webhook set. Bot is running...")

        print(">> Starting webhook listener...")
        await application.run_webhook(
            listen='0.0.0.0',
            port=int(os.environ.get('PORT', 10000)),
            url_path='/webhook',
            webhook_url=WEBHOOK_URL
        )
    except Exception as e:
        print(f"Telegram Bot Error: {str(e)}")

# === Main Execution ===
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))  # Match Render's detected port
    flask_thread = threading.Thread(
        target=lambda: app.run(host='0.0.0.0', port=port, use_reloader=False),
        daemon=True
    )
    flask_thread.start()
    print(f"📡 Flask server running on port {port}")

    # Remove nest_asyncio.apply()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def run_bot():
        await telegram_bot()

    try:
        print("🤖 Starting AI chatbot...")
        loop.run_until_complete(run_bot())
    except KeyboardInterrupt:
        print("\n🔴 Shutting down...")
        loop.close()