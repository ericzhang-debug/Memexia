"""
Database connections for Memexia backend.

Provides NebulaGraph, ChromaDB, and SQLAlchemy connections.
Each knowledge base uses a separate NebulaGraph Space for data isolation.
"""

import chromadb
from memexia_backend.config import settings
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Optional, Generator, Set
import logging
import time
import re

from nebula3.gclient.net import ConnectionPool
from nebula3.Config import Config as NebulaConfig
from nebula3.gclient.net.Session import Session as NebulaSession

from .services.nebula_deployer import auto_deploy_nebula

logger = logging.getLogger(__name__)

# Auto-deploy NebulaGraph if enabled
if settings.NEBULA_AUTO_DEPLOY:
    try:
        print("🔧 Checking NebulaGraph deployment...")
        auto_deploy_nebula()
    except Exception as e:
        print(f"⚠️ NebulaGraph auto-deployment failed: {e}")
        print("  Make sure NebulaGraph is manually installed and running")


# NebulaGraph Connection Pool
_nebula_pool: Optional[ConnectionPool] = None
_initialized_spaces: Set[str] = set()


def _kb_id_to_space_name(knowledge_base_id: str) -> str:
    """
    Convert knowledge base ID to valid NebulaGraph space name.

    Space names must start with a letter and contain only alphanumeric and underscores.
    """
    # Replace hyphens with underscores and add prefix
    safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', knowledge_base_id)
    return f"kb_{safe_name}"


def get_nebula_pool() -> ConnectionPool:
    """
    Get or create NebulaGraph connection pool.

    Returns:
        ConnectionPool instance
    """
    global _nebula_pool

    if _nebula_pool is None:
        config = NebulaConfig()
        config.max_connection_pool_size = 10
        config.timeout = 5000  # 5 seconds

        _nebula_pool = ConnectionPool()

        # Parse host from URI
        host = "127.0.0.1"
        if "://" in settings.NEBULA_URI:
            host = settings.NEBULA_URI.replace("nebula://", "").split(":")[0]

        # Initialize the connection pool
        ok = _nebula_pool.init([(host, settings.NEBULA_GRAPH_PORT)], config)

        if not ok:
            raise RuntimeError("Failed to initialize NebulaGraph connection pool")

        logger.info("✅ NebulaGraph connection pool initialized")

    return _nebula_pool


def ensure_space_exists(knowledge_base_id: str) -> None:
    """
    Ensure the NebulaGraph space for a knowledge base exists.
    Creates space and schema if not exists.

    Args:
        knowledge_base_id: Knowledge base ID
    """
    global _initialized_spaces

    space_name = _kb_id_to_space_name(knowledge_base_id)

    if space_name in _initialized_spaces:
        return

    pool = get_nebula_pool()
    session = pool.get_session(settings.NEBULA_USER, settings.NEBULA_PASSWORD)

    try:
        # Create space if not exists
        create_space_query = f"""
        CREATE SPACE IF NOT EXISTS `{space_name}` (
            partition_num=10,
            replica_factor=1,
            vid_type=FIXED_STRING(64)
        );
        """
        result = session.execute(create_space_query)
        if not result.is_succeeded():
            logger.warning(f"Space creation warning: {result.error_msg()}")

        # Wait for space to be ready
        time.sleep(2)

        # Use the space
        session.execute(f"USE `{space_name}`;")

        # Create Node tag (simplified - no knowledge_base_id needed)
        create_node_tag = """
        CREATE TAG IF NOT EXISTS Node (
            content string,
            node_type string,
            created_at string,
            updated_at string
        );
        """
        session.execute(create_node_tag)

        # Create RELATED edge type
        create_edge_type = """
        CREATE EDGE IF NOT EXISTS RELATED (
            relation_type string,
            weight int
        );
        """
        session.execute(create_edge_type)

        # Wait for schema to be ready, then create indexes
        time.sleep(1)

        try:
            session.execute("CREATE TAG INDEX IF NOT EXISTS idx_node_type ON Node(node_type(32));")
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")

        _initialized_spaces.add(space_name)
        logger.info(f"✅ NebulaGraph space '{space_name}' initialized for KB {knowledge_base_id}")

    except Exception as e:
        logger.error(f"Failed to initialize space for KB {knowledge_base_id}: {e}")
        raise
    finally:
        session.release()


def get_nebula_session_for_kb(knowledge_base_id: str) -> Generator[NebulaSession, None, None]:
    """
    Get a NebulaGraph session for a specific knowledge base.

    Each knowledge base has its own Space for data isolation.

    Args:
        knowledge_base_id: Knowledge base ID

    Yields:
        NebulaSession configured for the knowledge base's space
    """
    # Ensure space exists
    ensure_space_exists(knowledge_base_id)

    space_name = _kb_id_to_space_name(knowledge_base_id)
    pool = get_nebula_pool()
    session = pool.get_session(settings.NEBULA_USER, settings.NEBULA_PASSWORD)

    try:
        # Use the knowledge base's space
        result = session.execute(f"USE `{space_name}`;")
        if not result.is_succeeded():
            raise RuntimeError(f"Failed to use space {space_name}: {result.error_msg()}")
        yield session
    finally:
        session.release()


def delete_kb_space(knowledge_base_id: str) -> bool:
    """
    Delete the NebulaGraph space for a knowledge base.

    Args:
        knowledge_base_id: Knowledge base ID

    Returns:
        True if deleted successfully
    """
    global _initialized_spaces

    space_name = _kb_id_to_space_name(knowledge_base_id)
    pool = get_nebula_pool()
    session = pool.get_session(settings.NEBULA_USER, settings.NEBULA_PASSWORD)

    try:
        result = session.execute(f"DROP SPACE IF EXISTS `{space_name}`;")
        if result.is_succeeded():
            _initialized_spaces.discard(space_name)
            logger.info(f"Deleted space '{space_name}' for KB {knowledge_base_id}")
            return True
        else:
            logger.error(f"Failed to delete space: {result.error_msg()}")
            return False
    finally:
        session.release()


# ChromaDB Client
chroma_client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)


def get_chroma_collection():
    """Get or create the ChromaDB collection for nodes."""
    return chroma_client.get_or_create_collection(name="memexia_nodes")


def close_connections():
    """Close all database connections."""
    global _nebula_pool, _initialized_spaces

    if _nebula_pool is not None:
        _nebula_pool.close()
        _nebula_pool = None
        _initialized_spaces.clear()
        logger.info("NebulaGraph connection pool closed")


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
