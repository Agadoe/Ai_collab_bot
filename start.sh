#!/bin/bash

# Exit on any error
set -e

echo "🚀 Starting AI Collaboration Bot..."

# Check if required environment variables are set
if [ -z "$BOT_TOKEN" ]; then
    echo "❌ Error: BOT_TOKEN environment variable is required"
    exit 1
fi

echo "✅ Environment variables validated"

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
fi

echo "🤖 Starting Flask application..."
python main.py