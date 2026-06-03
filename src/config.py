"""
Configuration management for the Agentic SAP Assistant
Uses pydantic-settings for environment variable validation
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Supabase Configuration
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_key: str = os.getenv("SUPABASE_KEY", "")
    supabase_service_key: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    
    # Google Cloud / Gemini Configuration
    google_credentials: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    gemini_project_id: str = os.getenv("GEMINI_PROJECT_ID", "")
    gemini_location: str = os.getenv("GEMINI_LOCATION", "us-central1")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-004")
    
    # App Configuration - using getenv directly to avoid validation errors
    app_env: str = os.getenv("APP_ENV", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    vector_size: int = int(os.getenv("VECTOR_SIZE", "768"))
    match_threshold: float = float(os.getenv("MATCH_THRESHOLD", "0.7"))
    max_results: int = int(os.getenv("MAX_RESULTS", "5"))
    
    # Optional: OpenAI fallback
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # Pydantic configuration - allow extra fields to prevent validation errors
    model_config = ConfigDict(
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


# Create a single instance to be used across the application
try:
    settings = Settings()
    print(f"✅ Settings loaded successfully")
    print(f"   Environment: {settings.app_env}")
    print(f"   Supabase URL: {settings.supabase_url[:30]}..." if settings.supabase_url else "   Supabase URL: Not set")
except Exception as e:
    print(f"❌ Error loading settings: {e}")
    # Fallback to direct os.getenv for critical settings
    settings = None


# Helper function to validate settings
def validate_settings() -> bool:
    """Check if required settings are configured"""
    if not settings:
        return False
    
    missing = []
    if not settings.supabase_url:
        missing.append("SUPABASE_URL")
    if not settings.supabase_key:
        missing.append("SUPABASE_KEY")
    
    if missing:
        print(f"⚠️ Missing required environment variables: {', '.join(missing)}")
        return False
    
    return True


# Print status on import
if __name__ != "__main__":
    if validate_settings():
        print("✅ Configuration validated successfully")
    else:
        print("⚠️ Configuration incomplete - some features may not work")
