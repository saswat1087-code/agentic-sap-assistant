import os
import logging
import requests

logger = logging.getLogger(__name__)

class GeminiEmbedderWrapper:
    def __init__(self):
        # Dynamically look for either of the standard Google/Gemini environment variable names
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        
        if self.api_key:
            # Targeted to the modern mainline gemini-embedding-001 endpoint path
            self.url = f"https://generativelanguage.googleapis.com/v1/models/gemini-embedding-001:embedContent?key={self.api_key}"
            logger.info("✅ Native REST Google GenAI Embeddings client configured for gemini-embedding-001.")
        else:
            logger.warning("⚠️ WARNING: Neither GEMINI_API_KEY nor GOOGLE_API_KEY was found in environment variables.")
            self.url = None

    def generate(self, text: str) -> dict:
        """
        Generates a vector embedding array for the provided string context block.
        Returns a dictionary structure to perfectly satisfy streamlit_app.py expectations.
        """
        if not self.url:
            raise ValueError("Embedding client is not configured. Please verify your GEMINI_API_KEY configuration.")
        
        # Return a zeroed fallback array (768 dimensions) wrapped in the expected key structure if vacant
        if not text or not str(text).strip():
            return {"embedding": [0.0] * 768}
            
        try:
            # Construct the exact raw JSON request payload expected by the Google v1 REST API
            payload = {
                "model": "models/gemini-embedding-001",
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
            raw_values = response_json["embedding"]["values"]
            
            # CRITICAL FIX: Wrap the list of floats inside a dictionary under the 'embedding' key
            # This eliminates the KeyError on line 193 of streamlit_app.py
            return {"embedding": raw_values}
            
        except Exception as e:
            logger.error(f"Error executing raw REST vector embedding generation: {e}")
            raise e

# Instantiate the singleton instance to be consumed across the application stack
embedder = GeminiEmbedderWrapper()
