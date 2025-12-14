from neo4j import GraphDatabase
import chromadb
from memexia_backend.utils.config import settings
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Neo4j Driver
neo4j_driver = GraphDatabase.driver(
    settings.NEO4J_URI,
    auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
)

# ChromaDB Client
chroma_client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)

def get_neo4j_session():
    session = neo4j_driver.session()
    try:
        yield session
    finally:
        session.close()

def get_chroma_collection():
    # Get or create the collection for nodes
    return chroma_client.get_or_create_collection(name="memexia_nodes")

def close_connections():
    neo4j_driver.close()

engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
    if "sqlite" in settings.SQLALCHEMY_DATABASE_URL
    else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
