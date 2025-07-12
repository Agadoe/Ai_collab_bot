import os
import asyncio
import json
import uuid
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest

# Import our custom modules
from project_manager import project_manager, Project, ProjectTask, ProjectMilestone
from ai_collaboration import AICollaborationEngine

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

# === Data Structures ===
@dataclass
class AIAgent:
    name: str
    engine: str
    role: str
    description: str
    api_key: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 2000

@dataclass
class ConversationMessage:
    id: str
    timestamp: datetime
    sender: str  # 'user' or AI agent name
    content: str
    message_type: str  # 'text', 'code', 'file', 'command'
    metadata: Optional[Dict] = None

# === Global State ===
ai_agents: Dict[str, AIAgent] = {}
user_sessions: Dict[int, Dict] = {}  # user_id -> session data
collaboration_engine: Optional[AICollaborationEngine] = None

# === AI Engine Configuration ===
def initialize_ai_agents():
    """Initialize all available AI agents with their roles and capabilities"""
    global ai_agents
    
    ai_agents = {}
    
    # Only add agents that have valid API keys
    if OPENAI_API_KEY:
        ai_agents["openai_gpt4"] = AIAgent(
            name="GPT-4",
            engine="openai",
            role="General Assistant",
            description="Advanced reasoning and problem-solving",
            api_key=OPENAI_API_KEY,
            model="gpt-4",
            temperature=0.7
        )
        ai_agents["openai_gpt35"] = AIAgent(
            name="GPT-3.5",
            engine="openai",
            role="Code Assistant",
            description="Fast code generation and debugging",
            api_key=OPENAI_API_KEY,
            model="gpt-3.5-turbo",
            temperature=0.3
        )
    
    if GROQ_API_KEY:
        ai_agents["groq_llama"] = AIAgent(
            name="Llama-3",
            engine="groq",
            role="Creative Writer",
            description="Creative content generation and storytelling",
            api_key=GROQ_API_KEY,
            model="llama-3-8b-8192",
            temperature=0.8
        )
    
    if DEEPSEEK_API_KEY:
        ai_agents["deepseek"] = AIAgent(
            name="DeepSeek",
            engine="deepseek",
            role="Research Assistant",
            description="Research and analysis tasks",
            api_key=DEEPSEEK_API_KEY,
            model="deepseek-chat",
            temperature=0.5
        )
    
    if XAI_API_KEY:
        ai_agents["xai"] = AIAgent(
            name="xAI",
            engine="xai",
            role="Specialist",
            description="Specialized tasks and domain expertise",
            api_key=XAI_API_KEY,
            model="grok-beta",
            temperature=0.6
        )

# === AI Query Handler ===
async def query_ai_engine(agent_name: str, prompt: str, context: str = "", project_id: Optional[str] = None) -> str:
    """Query a specific AI engine with context"""
    if agent_name not in ai_agents:
        return f"Error: AI agent '{agent_name}' not found."
    
    agent = ai_agents[agent_name]
    
    # Build context-aware prompt
    full_prompt = f"""
Context: {context}

Current Task: {prompt}

Please respond as {agent.name}, a {agent.role}. {agent.description}

Response:"""
    
    try:
        if agent.engine == "openai":
            return await query_openai(agent, full_prompt)
        elif agent.engine == "groq":
            return await query_groq(agent, full_prompt)
        elif agent.engine == "deepseek":
            return await query_deepseek(agent, full_prompt)
        elif agent.engine == "xai":
            return await query_xai(agent, full_prompt)
        else:
            return f"Error: Unsupported engine '{agent.engine}'"
    except Exception as e:
        return f"Error querying {agent.name}: {str(e)}"

async def query_openai(agent: AIAgent, prompt: str) -> str:
    """Query OpenAI API"""
    try:
        import openai
        client = openai.OpenAI(api_key=agent.api_key)
        
        response = client.chat.completions.create(
            model=agent.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=agent.temperature,
            max_tokens=agent.max_tokens
        )
        return response.choices[0].message.content
    except ImportError:
        return "Error: OpenAI library not installed"
    except Exception as e:
        return f"Error querying OpenAI: {str(e)}"

async def query_groq(agent: AIAgent, prompt: str) -> str:
    """Query Groq API"""
    try:
        import groq
        client = groq.Groq(api_key=agent.api_key)
        
        response = client.chat.completions.create(
            model=agent.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=agent.temperature,
            max_tokens=agent.max_tokens
        )
        return response.choices[0].message.content
    except ImportError:
        return "Error: Groq library not installed"
    except Exception as e:
        return f"Error querying Groq: {str(e)}"

async def query_deepseek(agent: AIAgent, prompt: str) -> str:
    """Query DeepSeek API"""
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {agent.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": agent.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": agent.temperature,
            "max_tokens": agent.max_tokens
        }
        
        async with session.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=data
        ) as response:
            result = await response.json()
            return result["choices"][0]["message"]["content"]

async def query_xai(agent: AIAgent, prompt: str) -> str:
    """Query xAI API"""
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {agent.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": agent.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": agent.temperature,
            "max_tokens": agent.max_tokens
        }
        
        async with session.post(
            "https://api.x.ai/v1/chat/completions",
            headers=headers,
            json=data
        ) as response:
            result = await response.json()
            return result["choices"][0]["message"]["content"]

# === Project Management ===
def create_project(user_id: int, name: str, description: str, selected_agents: List[str]) -> Project:
    """Create a new collaborative project"""
    return project_manager.create_project(user_id, name, description, selected_agents)

def get_user_projects(user_id: int) -> List[Project]:
    """Get all projects for a user"""
    return project_manager.get_user_projects(user_id)

def add_message_to_project(project_id: str, sender: str, content: str, message_type: str = "text") -> None:
    """Add a message to project conversation history"""
    project = project_manager.get_project(project_id)
    if not project:
        return
    
    message = ConversationMessage(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(),
        sender=sender,
        content=content,
        message_type=message_type
    )
    
    project.conversation_history.append(asdict(message))
    project_manager.update_project(project_id, last_updated=datetime.now())

def get_project_context(project_id: str, limit: int = 10) -> str:
    """Get recent conversation context for a project"""
    project = project_manager.get_project(project_id)
    if not project:
        return ""
    
    recent_messages = project.conversation_history[-limit:] if project.conversation_history else []
    
    context = f"Project: {project.name}\nDescription: {project.description}\n\nRecent conversation:\n"
    for msg in recent_messages:
        context += f"{msg.get('sender', 'Unknown')}: {msg.get('content', '')}\n"
    
    return context

# === Collaborative AI Workflow ===
async def collaborative_ai_workflow(project_id: str, user_message: str) -> List[str]:
    """Execute collaborative workflow with multiple AIs"""
    project = project_manager.get_project(project_id)
    if not project:
        return ["Error: Project not found"]
    
    # Add user message to history
    add_message_to_project(project_id, "User", user_message)
    
    # Use the collaboration engine if available
    if collaboration_engine:
        return await collaboration_engine.start_collaboration(project_id, user_message)
    else:
        # Fallback to simple workflow
        responses = []
        context = get_project_context(project_id)
        
        # Have each AI agent contribute based on their role
        for agent_name in project.ai_agents:
            if agent_name in ai_agents:
                agent = ai_agents[agent_name]
                
                # Create role-specific prompt
                role_prompt = f"""
As {agent.name} ({agent.role}), analyze the current project and user request.
Consider your expertise: {agent.description}

User Request: {user_message}

Please provide your contribution to this collaborative effort.
"""
                
                response = await query_ai_engine(agent_name, role_prompt, context, project_id)
                responses.append(f"🤖 {agent.name} ({agent.role}):\n{response}")
                
                # Add AI response to project history
                add_message_to_project(project_id, agent.name, response)
        
        return responses

# === Flask Server Setup ===
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Collaborative AI Bot is Running - Visit https://t.me/your_bot to start collaborating!"

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

# === Telegram Handlers ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message with main menu"""
    keyboard = [
        [InlineKeyboardButton("🆕 Create New Project", callback_data="create_project")],
        [InlineKeyboardButton("📋 My Projects", callback_data="list_projects")],
        [InlineKeyboardButton("🤖 AI Agents", callback_data="show_agents")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🌟 Welcome to the Collaborative AI Bot!\n\n"
        "I can help you create projects where multiple AI agents work together.\n"
        "Choose an option below to get started:",
        reply_markup=reply_markup
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "create_project":
        await show_create_project_menu(query, context)
    elif query.data == "list_projects":
        await show_user_projects(query, context)
    elif query.data == "show_agents":
        await show_ai_agents(query, context)
    elif query.data == "help":
        await show_help(query, context)
    elif query.data.startswith("select_agent_"):
        agent_name = query.data.replace("select_agent_", "")
        await handle_agent_selection(query, context, agent_name)
    elif query.data.startswith("project_"):
        project_id = query.data.replace("project_", "")
        await show_project_details(query, context, project_id)
    elif query.data == "back_to_main":
        await show_main_menu(query, context)

async def show_create_project_menu(query, context):
    """Show project creation menu"""
    keyboard = [
        [InlineKeyboardButton("📝 Start Project Creation", callback_data="start_project_creation")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🆕 Create New Collaborative Project\n\n"
        "You'll be able to:\n"
        "• Choose multiple AI agents\n"
        "• Define project goals\n"
        "• Start collaborative work\n\n"
        "Ready to begin?",
        reply_markup=reply_markup
    )

async def show_ai_agents(query, context):
    """Show available AI agents"""
    keyboard = []
    for agent_name, agent in ai_agents.items():
        keyboard.append([InlineKeyboardButton(
            f"🤖 {agent.name} - {agent.role}",
            callback_data=f"agent_info_{agent_name}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_to_main")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🤖 Available AI Agents\n\n"
        "Each agent has specific roles and capabilities:",
        reply_markup=reply_markup
    )

async def show_user_projects(query, context):
    """Show user's projects"""
    user_id = query.from_user.id
    user_projects = get_user_projects(user_id)
    
    if not user_projects:
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "📋 No projects found.\n\n"
            "Create your first collaborative project!",
            reply_markup=reply_markup
        )
        return
    
    keyboard = []
    for project in user_projects:
        keyboard.append([InlineKeyboardButton(
            f"📁 {project.name} ({project.status})",
            callback_data=f"project_{project.id}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_to_main")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"📋 Your Projects ({len(user_projects)})\n\n"
        "Select a project to view details and continue collaboration:",
        reply_markup=reply_markup
    )

async def show_project_details(query, context, project_id):
    """Show project details and conversation"""
    project = project_manager.get_project(project_id)
    if not project:
        await query.edit_message_text("❌ Project not found.")
        return
    
    # Show recent conversation
    recent_messages = project.conversation_history[-5:] if project.conversation_history else []
    conversation_text = ""
    for msg in recent_messages:
        sender = msg.get('sender', 'Unknown')
        content = msg.get('content', '')[:100]
        conversation_text += f"**{sender}**: {content}...\n\n"
    
    keyboard = [
        [InlineKeyboardButton("💬 Continue Chat", callback_data=f"chat_{project_id}")],
        [InlineKeyboardButton("📊 Project Info", callback_data=f"info_{project_id}")],
        [InlineKeyboardButton("🔙 Back to Projects", callback_data="list_projects")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"📁 Project: {project.name}\n"
        f"📝 Description: {project.description}\n"
        f"🤖 AI Agents: {', '.join(project.ai_agents)}\n"
        f"📅 Created: {project.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
        f"Recent conversation:\n{conversation_text}",
        reply_markup=reply_markup
    )

async def show_main_menu(query, context):
    """Show main menu"""
    keyboard = [
        [InlineKeyboardButton("🆕 Create New Project", callback_data="create_project")],
        [InlineKeyboardButton("📋 My Projects", callback_data="list_projects")],
        [InlineKeyboardButton("🤖 AI Agents", callback_data="show_agents")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🌟 Collaborative AI Bot\n\n"
        "Choose an option to get started:",
        reply_markup=reply_markup
    )

async def handle_agent_selection(query, context, agent_name):
    """Handle AI agent selection for project creation"""
    if agent_name not in ai_agents:
        await query.edit_message_text("❌ AI agent not found.")
        return
    
    agent = ai_agents[agent_name]
    
    keyboard = [
        [InlineKeyboardButton("✅ Select This Agent", callback_data=f"confirm_agent_{agent_name}")],
        [InlineKeyboardButton("🔙 Back to Agents", callback_data="show_agents")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"🤖 {agent.name}\n\n"
        f"**Role**: {agent.role}\n"
        f"**Description**: {agent.description}\n"
        f"**Engine**: {agent.engine}\n"
        f"**Model**: {agent.model}\n\n"
        f"Would you like to add this agent to your project?",
        reply_markup=reply_markup
    )

async def show_help(query, context):
    """Show help information"""
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    help_text = """
❓ How to Use Collaborative AI Bot

1. **Create a Project**
   - Choose multiple AI agents
   - Define your project goals
   - Start collaborative work

2. **AI Agents Work Together**
   - Each agent contributes based on their role
   - Agents build upon each other's work
   - Maintain conversation context

3. **Project Management**
   - Track progress across sessions
   - View conversation history
   - Manage multiple projects

4. **Available Commands**
   /start - Main menu
   /new - Create new project
   /projects - List your projects
   /help - Show this help

Ready to start collaborating? 🚀
"""
    
    await query.edit_message_text(help_text, reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    user_id = update.message.from_user.id
    user_message = update.message.text
    
    # Check if user is in a project chat session
    if user_id in user_sessions and user_sessions[user_id].get('active_project'):
        project_id = user_sessions[user_id]['active_project']
        
        # Execute collaborative workflow
        responses = await collaborative_ai_workflow(project_id, user_message)
        
        # Send responses from all AI agents
        for response in responses:
            await update.message.reply_text(response)
        
        # Send summary of collaboration
        await update.message.reply_text(
            f"🤝 Collaboration complete! {len(responses)} AI agents contributed to your project."
        )
    else:
        # Default response - suggest creating a project
        keyboard = [
            [InlineKeyboardButton("🆕 Create New Project", callback_data="create_project")],
            [InlineKeyboardButton("📋 My Projects", callback_data="list_projects")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "💬 I'm ready to help you with collaborative AI work!\n\n"
            "To get started, create a new project or select an existing one:",
            reply_markup=reply_markup
        )

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
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    return application

async def set_webhook():
    await application.bot.set_webhook(
        url=WEBHOOK_URL,
        drop_pending_updates=True
    )

# === Main Execution ===
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    
    # Initialize AI agents
    initialize_ai_agents()
    
    # Initialize collaboration engine
    collaboration_engine = AICollaborationEngine(ai_agents, project_manager)
    
    # Initialize the bot
    initialize_bot()
    
    # Create a new event loop for the bot
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Set webhook
    loop.run_until_complete(set_webhook())
    print(f"Webhook set at {WEBHOOK_URL}")
    print(f"Initialized {len(ai_agents)} AI agents for collaboration")
    print("🤝 Collaborative AI system ready!")
    
    # Run Flask app
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)