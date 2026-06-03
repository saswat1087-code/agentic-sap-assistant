from typing import List
import logging
from langchain_google_vertexai import VertexAIEmbeddings
from src.config import settings

logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    def __init__(self):
        self.embeddings = VertexAIEmbeddings(
            model_name=settings.embedding_model,
            project=settings.gemini_project_id,
            location=settings.gemini_location
        )
        logger.info(f"Embedding model initialized: {settings.embedding_model}")
    
    def generate(self, text: str) -> List[float]:
        """Generate embedding for a text"""
        try:
            # Truncate long text (Gemini embedding limit is ~2048 tokens)
            if len(text) > 4000:
                text = text[:4000]
            
            embedding = self.embeddings.embed_query(text)
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * settings.vector_size
    
    def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        try:
            embeddings = self.embeddings.embed_documents(texts)
            return embeddings
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            return [[0.0] * settings.vector_size for _ in texts]

# Singleton instance
embedder = EmbeddingGenerator()
