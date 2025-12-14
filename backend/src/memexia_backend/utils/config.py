import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
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
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
