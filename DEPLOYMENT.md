# 🚀 Deployment Checklist

## Pre-Deployment Checklist

### ✅ Required Setup
- [ ] Telegram bot created via @BotFather
- [ ] Bot token obtained and ready
- [ ] At least one AI API key obtained (OpenAI, Groq, etc.)
- [ ] GitHub repository created and code pushed
- [ ] Render.com account created

### ✅ Environment Variables
Set these in Render.com dashboard:

**Required:**
- [ ] `BOT_TOKEN` - Your Telegram bot token
- [ ] `WEBHOOK_URL` - Will be set automatically by Render.com

**Optional (but recommended):**
- [ ] `OPENAI_API_KEY` - OpenAI API key
- [ ] `GROQ_API_KEY` - Groq API key
- [ ] `OPENROUTER_API_KEY` - OpenRouter API key
- [ ] `DEEPSEEK_API_KEY` - DeepSeek API key
- [ ] `XAI_API_KEY` - X.AI API key

### ✅ Render.com Configuration
- [ ] Connect GitHub repository to Render.com
- [ ] Create new Web Service
- [ ] Set build command: `pip install -r requirements.txt`
- [ ] Set start command: `python main.py`
- [ ] Set environment variables
- [ ] Deploy the service

## Post-Deployment Checklist

### ✅ Verification
- [ ] Service is running (green status in Render.com)
- [ ] Health check endpoint works: `https://your-app.onrender.com/health`
- [ ] Home page loads: `https://your-app.onrender.com/`
- [ ] Webhook URL is accessible: `https://your-app.onrender.com/webhook`

### ✅ Bot Testing
- [ ] Send `/start` command to your bot
- [ ] Bot responds with welcome message
- [ ] Send `/engines` command to see available engines
- [ ] Test message handling with configured AI engines
- [ ] Test engine switching with `/use <engine>` command

### ✅ Troubleshooting
If issues occur:
- [ ] Check Render.com logs for errors
- [ ] Verify all environment variables are set correctly
- [ ] Ensure API keys are valid and have sufficient credits
- [ ] Check webhook URL is correctly formatted
- [ ] Verify bot token is correct

## 🔧 Common Issues & Solutions

### Bot Not Responding
1. Check if `BOT_TOKEN` is set correctly
2. Verify webhook URL is accessible
3. Check Render.com logs for errors
4. Ensure service is running (not sleeping)

### AI Engines Not Working
1. Verify at least one API key is configured
2. Check API key validity and credits
3. Test API key with a simple curl request
4. Check internet connectivity

### Deployment Fails
1. Check Python version compatibility (3.11+)
2. Verify all dependencies in `requirements.txt`
3. Check build logs for specific errors
4. Ensure no syntax errors in code

## 📞 Support
- Check Render.com documentation
- Review troubleshooting section in README.md
- Check application logs in Render.com dashboard