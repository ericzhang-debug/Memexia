from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Neo4j Settings
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"

    # ChromaDB Settings
    CHROMA_DB_PATH: str = "./chroma_db"

    # Model Settings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # SQL Database Settings
    SQLALCHEMY_DATABASE_URL: str = "sqlite:///./memexia.db"

    # Security
    SECRET_KEY: str = "your-secret-key-keep-it-secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Email Settings
    ENABLE_EMAIL_VERIFICATION: bool = False
    SMTP_SERVER: str = "smtp.example.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = "user@example.com"
    SMTP_PASSWORD: str = "password"
    EMAIL_FROM: str = "noreply@memexia.local"
    FRONTEND_URL: str = "http://localhost:5173"

    # Superuser Settings
    # IMPORTANT: Change these in production via environment variables!
    SUPERUSER_USERNAME: str = "admin"
    SUPERUSER_EMAIL: str = "admin@memexia.local"
    SUPERUSER_PASSWORD: Optional[str] = None  # Must be set via env var in production

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
