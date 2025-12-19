"""
Database connections for Memexia backend.

Provides ChromaDB and SQLAlchemy connections.
Graph database is handled by the services.graph module.
"""

import chromadb
from memexia_backend.config import settings
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from memexia_backend.logger import logger


# ChromaDB Client
chroma_client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)


def get_chroma_collection():
    """Get or create the ChromaDB collection for nodes."""
    return chroma_client.get_or_create_collection(name="memexia_nodes")


# SQLAlchemy setup
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
    if "sqlite" in settings.SQLALCHEMY_DATABASE_URL
    else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Get SQLAlchemy database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def close_connections():
    """Close all database connections."""
    from memexia_backend.services.graph import close_graph_db

    close_graph_db()
    logger.info("All database connections closed")
