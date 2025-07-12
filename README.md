# 🤖 AI Collaboration Bot

A multi-engine AI chatbot with collaborative capabilities, supporting multiple AI providers including OpenAI, Groq, OpenRouter, DeepSeek, and X.AI.

## 🚀 Features

- **Multi-Engine Support**: Switch between different AI engines
- **Telegram Integration**: Full Telegram bot functionality
- **Webhook Support**: Secure webhook-based communication
- **Health Monitoring**: Built-in health check endpoints
- **Environment-Based Configuration**: Easy configuration via environment variables

## 🛠️ Setup

### Prerequisites

- Python 3.11+
- Telegram Bot Token (from @BotFather)
- At least one AI API key (OpenAI, Groq, OpenRouter, DeepSeek, or X.AI)

### Local Development

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd ai-collaboration-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables**
   ```bash
   export BOT_TOKEN="your_telegram_bot_token"
   export WEBHOOK_URL="https://your-domain.com/webhook"
   export OPENAI_API_KEY="your_openai_api_key"
   # Add other API keys as needed
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

## 🌐 Deployment on Render.com

### Method 1: Using render.yaml (Recommended)

1. **Push your code to GitHub**
2. **Connect your repository to Render.com**
3. **Render will automatically detect the `render.yaml` file**
4. **Set environment variables in Render dashboard**

### Method 2: Manual Setup

1. **Create a new Web Service on Render.com**
2. **Connect your GitHub repository**
3. **Configure the service:**
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
   - **Environment**: Python 3.11

### Required Environment Variables

Set these in your Render.com dashboard:

| Variable | Description | Required |
|----------|-------------|----------|
| `BOT_TOKEN` | Telegram bot token from @BotFather | ✅ Yes |
| `WEBHOOK_URL` | Your Render.com URL + `/webhook` | ✅ Yes |
| `OPENAI_API_KEY` | OpenAI API key | ❌ No (but recommended) |
| `GROQ_API_KEY` | Groq API key | ❌ No |
| `OPENROUTER_API_KEY` | OpenRouter API key | ❌ No |
| `DEEPSEEK_API_KEY` | DeepSeek API key | ❌ No |
| `XAI_API_KEY` | X.AI API key | ❌ No |
| `API_ID` | Telegram API ID (for Telethon) | ❌ No |
| `API_HASH` | Telegram API Hash (for Telethon) | ❌ No |
| `PHONE` | Phone number (for Telethon) | ❌ No |

### Webhook Configuration

After deployment, set your webhook URL:
```
https://your-app-name.onrender.com/webhook
```

## 📱 Bot Commands

- `/start` - Show welcome message and available commands
- `/engines` - List available AI engines and their status
- `/use <engine>` - Switch to a specific AI engine (e.g., `/use openai`)

## 🔧 API Endpoints

- `GET /` - Home page
- `GET /health` - Health check endpoint
- `POST /webhook` - Telegram webhook endpoint

## 🐛 Troubleshooting

### Common Issues

1. **Bot not responding**
   - Check if `BOT_TOKEN` is set correctly
   - Verify webhook URL is accessible
   - Check Render.com logs for errors

2. **AI engines not working**
   - Ensure at least one API key is configured
   - Check API key validity
   - Verify internet connectivity

3. **Deployment fails**
   - Check Python version compatibility
   - Verify all dependencies are in `requirements.txt`
   - Check Render.com build logs

### Logs

Check Render.com logs for detailed error information:
1. Go to your service dashboard
2. Click on "Logs" tab
3. Look for error messages and stack traces

## 📄 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For issues and questions:
- Check the troubleshooting section
- Review Render.com documentation
- Open an issue on GitHub 
