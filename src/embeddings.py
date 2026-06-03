import os
import logging
from langchain_google_genai import GoogleGenerativeAIEmbeddings

logger = logging.getLogger(__name__)

class GeminiEmbedderWrapper:
    def __init__(self):
        # Dynamically look for either of the standard Google/Gemini environment variable names
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        
        if self.api_key:
            try:
                # Initializing with the prefix-free model identifier resolves the unexpected format error
                self.client = GoogleGenerativeAIEmbeddings(
                    model="text-embedding-004",
                    google_api_key=self.api_key
                )
                logger.info("✅ Gemini Embeddings client initialized successfully.")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Gemini GenAI client: {e}")
                self.client = None
        else:
            logger.warning("⚠️ WARNING: Neither GEMINI_API_KEY nor GOOGLE_API_KEY was found in environment variables.")
            self.client = None

    def generate(self, text: str) -> list:
        """
        Generates a vector embedding array for the provided string context block.
        Matches the interface expected by the core Streamlit ingest loops.
        """
        if not self.client:
            raise ValueError("Embedding client is not initialized. Please verify your GEMINI_API_KEY configuration.")
        
        if not text or not str(text).strip():
            # Return a zeroed fallback array (768 dimensions) if string context is completely vacant
            return [0.0] * 768
            
        try:
            # LangChain's embed_query returns a standard Python list of floats
            return self.client.embed_query(str(text))
        except Exception as e:
            logger.error(f"Error executing vector embedding generation: {e}")
            raise e

# Instantiate the singleton instance to be consumed across the application stack
embedder = GeminiEmbedderWrapper()
