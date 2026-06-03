import os
import logging
import requests

logger = logging.getLogger(__name__)

class GeminiEmbedderWrapper:
    def __init__(self):
        # Dynamically look for either of the standard Google/Gemini environment variable names
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        
        if self.api_key:
            # Explicitly target the verified v1beta routing directory for text-embedding-004
            self.url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={self.api_key}"
            logger.info("✅ Native REST Google GenAI Embeddings client configured successfully.")
        else:
            logger.warning("⚠️ WARNING: Neither GEMINI_API_KEY nor GOOGLE_API_KEY was found in environment variables.")
            self.url = None

    def generate(self, text: str) -> list:
        """
        Generates a vector embedding array for the provided string context block.
        Matches the interface expected by the core Streamlit ingest loops.
        """
        if not self.url:
            raise ValueError("Embedding client is not configured. Please verify your GEMINI_API_KEY configuration.")
        
        if not text or not str(text).strip():
            # Return a zeroed fallback array (768 dimensions) if string context is completely vacant
            return [0.0] * 768
            
        try:
            # Construct the exact raw JSON request payload expected by the Google v1beta REST API
            payload = {
                "model": "models/text-embedding-004",
                "content": {
                    "parts": [{
                        "text": str(text)
                    }]
                }
            }
            
            response = requests.post(self.url, json=payload, headers={"Content-Type": "application/json"})
            
            # Handle standard error status codes explicitly
            if response.status_code != 200:
                logger.error(f"Google API returned error status {response.status_code}: {response.text}")
                raise ValueError(f"Google API Error: {response.text}")
                
            response_json = response.json()
            
            # Extract the raw flat list of floats directly from the response body mapping layer
            return response_json["embedding"]["values"]
            
        except Exception as e:
            logger.error(f"Error executing raw REST vector embedding generation: {e}")
            raise e

# Instantiate the singleton instance to be consumed across the application stack
embedder = GeminiEmbedderWrapper()
