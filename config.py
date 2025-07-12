"""
Configuration file for Collaborative AI Bot
Centralizes all settings and environment variables
"""

import os
from typing import Dict, Any, Optional

class Config:
    """Configuration class for the Collaborative AI Bot"""
    
    # === Bot Configuration ===
    BOT_TOKEN: str = os.getenv('BOT_TOKEN', '')
    WEBHOOK_URL: str = os.getenv('WEBHOOK_URL', '')
    PORT: int = int(os.getenv('PORT', 10000))
    
    # === AI API Keys ===
    OPENAI_API_KEY: Optional[str] = os.getenv('OPENAI_API_KEY')
    GROQ_API_KEY: Optional[str] = os.getenv('GROQ_API_KEY')
    OPENROUTER_API_KEY: Optional[str] = os.getenv('OPENROUTER_API_KEY')
    DEEPSEEK_API_KEY: Optional[str] = os.getenv('DEEPSEEK_API_KEY')
    XAI_API_KEY: Optional[str] = os.getenv('XAI_API_KEY')
    
    # === Telegram Client (Optional) ===
    API_ID: Optional[str] = os.getenv('API_ID')
    API_HASH: Optional[str] = os.getenv('API_HASH')
    PHONE: Optional[str] = os.getenv('PHONE')
    
    # === Storage Configuration ===
    PROJECTS_STORAGE_PATH: str = os.getenv('PROJECTS_STORAGE_PATH', 'projects')
    LOGS_PATH: str = os.getenv('LOGS_PATH', 'logs')
    
    # === Collaboration Settings ===
    MAX_AGENTS_PER_PROJECT: int = int(os.getenv('MAX_AGENTS_PER_PROJECT', 5))
    MAX_MESSAGES_PER_PROJECT: int = int(os.getenv('MAX_MESSAGES_PER_PROJECT', 1000))
    COLLABORATION_TIMEOUT: int = int(os.getenv('COLLABORATION_TIMEOUT', 300))  # seconds
    
    # === AI Model Defaults ===
    DEFAULT_TEMPERATURE: float = float(os.getenv('DEFAULT_TEMPERATURE', 0.7))
    DEFAULT_MAX_TOKENS: int = int(os.getenv('DEFAULT_MAX_TOKENS', 2000))
    
    # === Feature Flags ===
    ENABLE_COLLABORATION_ENGINE: bool = os.getenv('ENABLE_COLLABORATION_ENGINE', 'true').lower() == 'true'
    ENABLE_PROJECT_STORAGE: bool = os.getenv('ENABLE_PROJECT_STORAGE', 'true').lower() == 'true'
    ENABLE_ANALYTICS: bool = os.getenv('ENABLE_ANALYTICS', 'true').lower() == 'true'
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        if not cls.BOT_TOKEN:
            print("❌ Error: BOT_TOKEN is required")
            return False
        
        if not cls.WEBHOOK_URL:
            print("⚠️  Warning: WEBHOOK_URL not set (webhook mode disabled)")
        
        # Check if at least one AI API key is provided
        ai_keys = [
            cls.OPENAI_API_KEY,
            cls.GROQ_API_KEY,
            cls.DEEPSEEK_API_KEY,
            cls.XAI_API_KEY
        ]
        
        if not any(ai_keys):
            print("❌ Error: At least one AI API key is required")
            return False
        
        return True
    
    @classmethod
    def get_available_ai_services(cls) -> Dict[str, bool]:
        """Get dictionary of available AI services"""
        return {
            'openai': bool(cls.OPENAI_API_KEY),
            'groq': bool(cls.GROQ_API_KEY),
            'deepseek': bool(cls.DEEPSEEK_API_KEY),
            'xai': bool(cls.XAI_API_KEY),
            'openrouter': bool(cls.OPENROUTER_API_KEY)
        }
    
    @classmethod
    def print_config_summary(cls):
        """Print a summary of the current configuration"""
        print("🤖 Collaborative AI Bot Configuration")
        print("=" * 40)
        print(f"Bot Token: {'✅ Set' if cls.BOT_TOKEN else '❌ Missing'}")
        print(f"Webhook URL: {'✅ Set' if cls.WEBHOOK_URL else '❌ Missing'}")
        print(f"Port: {cls.PORT}")
        print()
        print("AI Services:")
        services = cls.get_available_ai_services()
        for service, available in services.items():
            status = "✅ Available" if available else "❌ Not configured"
            print(f"  {service.upper()}: {status}")
        print()
        print("Features:")
        print(f"  Collaboration Engine: {'✅ Enabled' if cls.ENABLE_COLLABORATION_ENGINE else '❌ Disabled'}")
        print(f"  Project Storage: {'✅ Enabled' if cls.ENABLE_PROJECT_STORAGE else '❌ Disabled'}")
        print(f"  Analytics: {'✅ Enabled' if cls.ENABLE_ANALYTICS else '❌ Disabled'}")
        print("=" * 40)

# Development configuration
class DevelopmentConfig(Config):
    """Development-specific configuration"""
    DEBUG = True
    LOG_LEVEL = "DEBUG"
    COLLABORATION_TIMEOUT = 60  # Shorter timeout for development

# Production configuration
class ProductionConfig(Config):
    """Production-specific configuration"""
    DEBUG = False
    LOG_LEVEL = "INFO"
    ENABLE_ANALYTICS = True

# Testing configuration
class TestingConfig(Config):
    """Testing-specific configuration"""
    DEBUG = True
    LOG_LEVEL = "DEBUG"
    PROJECTS_STORAGE_PATH = "test_projects"
    ENABLE_COLLABORATION_ENGINE = False  # Disable for faster tests

# Configuration factory
def get_config(environment: Optional[str] = None) -> Config:
    """Get configuration based on environment"""
    if not environment:
        environment = os.getenv('FLASK_ENV', 'development')
    
    configs = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestingConfig
    }
    
    return configs.get(environment, DevelopmentConfig)