import os
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)

class GeminiEmbedderWrapper:
    def __init__(self):
        # Dynamically look for either of the standard Google/Gemini environment variable names
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        
        if self.api_key:
            try:
                # Configure the native Google GenAI SDK directly
                genai.configure(api_key=self.api_key)
                # Using the exact absolute path identifier with the native SDK bypasses translation layers
                self.model_name = "models/text-embedding-004"
                logger.info("✅ Native Google GenAI Embeddings client configured successfully.")
            except Exception as e:
                logger.error(f"❌ Failed to configure native Google GenAI client: {e}")
                self.model_name = None
        else:
            logger.warning("⚠️ WARNING: Neither GEMINI_API_KEY nor GOOGLE_API_KEY was found in environment variables.")
            self.model_name = None

    def generate(self, text: str) -> list:
        """
        Generates a vector embedding array for the provided string context block.
        Matches the interface expected by the core Streamlit ingest loops.
        """
        if not self.model_name:
            raise ValueError("Embedding client is not configured. Please verify your GEMINI_API_KEY configuration.")
        
        if not text or not str(text).strip():
            # Return a zeroed fallback array (768 dimensions) if string context is completely vacant
            return [0.0] * 768
            
        try:
            # Call the native SDK embedding generation function directly
            response = genai.embed_content(
                model=self.model_name,
                content=str(text),
                task_type="retrieval_document"
            )
            # Extract the raw vector list of floats from the response payload array
            return response['embedding']
        except Exception as e:
            logger.error(f"Error executing native vector embedding generation: {e}")
            raise e

# Instantiate the singleton instance to be consumed across the application stack
embedder = GeminiEmbedderWrapper()
