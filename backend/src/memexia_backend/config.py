from typing import Literal
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Graph Database Backend Selection
    # Options: "kuzu" (embedded, default) or "nebula" (distributed)
    GRAPH_DB_TYPE: Literal["kuzu", "nebula"] = "kuzu"

    # Kuzu Settings (embedded graph database)
    KUZU_DB_PATH: str = "./data/kuzu_db"

    # NebulaGraph Settings (distributed graph database)
    # Only needed if GRAPH_DB_TYPE = "nebula"
    NEBULA_HOST: str = "127.0.0.1"
    NEBULA_PORT: int = 9669
    NEBULA_USER: str = "root"
    NEBULA_PASSWORD: str = "nebula"

    # ChromaDB Settings
    CHROMA_DB_PATH: str = "./data/chroma_db"

    # Model Settings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # SQL Database Settings
    SQLALCHEMY_DATABASE_URL: str = "sqlite:///./data/memexia.db"

    # Security
    SECRET_KEY: str = "your-secret-key-keep-it-secret"
    JWT_ALGORITHM: str = "HS256"
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
    SUPERUSER_PASSWORD: str

    # Logging Settings
    LOG_LEVEL: str = "INFO"

    # OpenAI API Settings
    # Supports OpenAI-compatible APIs (OpenAI, Azure, local models, etc.)
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_MAX_TOKENS: int = 2048
    OPENAI_TEMPERATURE: float = 0.7

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()  # type: ignore
