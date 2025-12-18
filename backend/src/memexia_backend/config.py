from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    NEBULA_USER: str = "root"
    NEBULA_PASSWORD: str = "nebula"
    NEBULA_URI: str = "nebula://localhost:9669"
    NEBULA_GRAPH_PORT: int = 9669
    NEBULA_META_PORT: int = 9559
    NEBULA_STORAGE_PORT: int = 9779
    NEBULA_AUTO_DEPLOY: bool = True  # Enable auto-deployment
    NEBULA_VERSION: str = "v3.6.0"
    NEBULA_DEPLOY_PATH: str = "./data/nebula"

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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings() #type: ignore
