import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Supabase
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_key: str = os.getenv("SUPABASE_KEY", "")
    supabase_service_key: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    
    # Google Cloud / Gemini
    google_credentials: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    gemini_project_id: str = os.getenv("GEMINI_PROJECT_ID", "")
    gemini_location: str = os.getenv("GEMINI_LOCATION", "us-central1")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-004")
    
    # App settings
    vector_size: int = int(os.getenv("VECTOR_SIZE", "768"))
    match_threshold: float = float(os.getenv("MATCH_THRESHOLD", "0.7"))
    max_results: int = int(os.getenv("MAX_RESULTS", "5"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Optional: OpenAI fallback
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
