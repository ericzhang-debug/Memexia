from sentence_transformers import SentenceTransformer
from memexia_backend.utils.config import settings

class EmbeddingService:
    def __init__(self):
        # Load model lazily or on startup
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)

    def generate_embedding(self, text: str):
        return self.model.encode(text).tolist()

# Singleton instance
embedding_service = EmbeddingService()
