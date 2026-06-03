"""
Embedding generation module for SAP incidents
Uses Google VertexAI embeddings for semantic search
"""

from typing import List
import logging
from src.config import settings

logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    """Generate embeddings for text using Google VertexAI"""
    
    def __init__(self):
        """Initialize the embedding model"""
        self.embeddings = None
        self._initialize_embeddings()
    
    def _initialize_embeddings(self):
        """Initialize the VertexAI embeddings with fallback options"""
        try:
            # Try newer import path first
            from langchain_google_vertexai import VertexAIEmbeddings
            
            self.embeddings = VertexAIEmbeddings(
                model_name=settings.embedding_model,
                project=settings.gemini_project_id,
                location=settings.gemini_location
            )
            logger.info(f"✅ Embedding model initialized: {settings.embedding_model}")
            
        except ImportError as e:
            logger.error(f"Failed to import VertexAIEmbeddings: {e}")
            logger.info("Attempting alternative import...")
            
            try:
                # Try alternative import for older versions
                from langchain_google_vertexai.embeddings import VertexAIEmbeddings
                
                self.embeddings = VertexAIEmbeddings(
                    model_name=settings.embedding_model,
                    project=settings.gemini_project_id,
                    location=settings.gemini_location
                )
                logger.info(f"✅ Embedding model initialized (alternative): {settings.embedding_model}")
                
            except ImportError as e2:
                logger.error(f"Failed to initialize embeddings: {e2}")
                logger.warning("⚠️ Embeddings will use zero vectors - similarity search will not work properly")
                self.embeddings = None
    
    def generate(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Input text to generate embedding for
            
        Returns:
            List of floats representing the embedding vector
        """
        if not self.embeddings:
            logger.warning("Embeddings not initialized, returning zero vector")
            return [0.0] * settings.vector_size
        
        try:
            # Truncate long text (VertexAI embedding limit is ~2048 tokens)
            # 4000 characters is approximately 1000-1500 tokens
            if len(text) > 4000:
                text = text[:4000]
                logger.debug(f"Text truncated to {len(text)} characters")
            
            embedding = self.embeddings.embed_query(text)
            
            # Validate embedding length
            if len(embedding) != settings.vector_size:
                logger.warning(f"Embedding length mismatch: expected {settings.vector_size}, got {len(embedding)}")
                # Pad or truncate as needed
                if len(embedding) > settings.vector_size:
                    embedding = embedding[:settings.vector_size]
                else:
                    embedding = embedding + [0.0] * (settings.vector_size - len(embedding))
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * settings.vector_size
    
    def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch
        
        Args:
            texts: List of input texts
            
        Returns:
            List of embedding vectors
        """
        if not self.embeddings:
            logger.warning("Embeddings not initialized, returning zero vectors")
            return [[0.0] * settings.vector_size for _ in texts]
        
        try:
            # Truncate long texts
            truncated_texts = []
            for text in texts:
                if len(text) > 4000:
                    text = text[:4000]
                truncated_texts.append(text)
            
            embeddings = self.embeddings.embed_documents(truncated_texts)
            
            # Validate each embedding
            for i, embedding in enumerate(embeddings):
                if len(embedding) != settings.vector_size:
                    logger.warning(f"Embedding {i} length mismatch")
                    if len(embedding) > settings.vector_size:
                        embeddings[i] = embedding[:settings.vector_size]
                    else:
                        embeddings[i] = embedding + [0.0] * (settings.vector_size - len(embedding))
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            return [[0.0] * settings.vector_size for _ in texts]
    
    def is_available(self) -> bool:
        """Check if embeddings are properly initialized"""
        return self.embeddings is not None


# ==================== SINGLETON INSTANCE ====================

# Create a single instance to be used across the application
try:
    embedder = EmbeddingGenerator()
    if embedder.is_available():
        logger.info("✅ Embedding generator ready")
    else:
        logger.warning("⚠️ Embedding generator initialized but not functional")
except Exception as e:
    logger.error(f"❌ Failed to create embedding generator: {e}")
    embedder = None
