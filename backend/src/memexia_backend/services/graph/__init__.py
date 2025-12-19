"""
Graph database backend module.

Provides a pluggable graph database backend with support for:
- Kuzu (embedded, default)
- NebulaGraph (distributed)

Usage:
    from memexia_backend.services.graph import get_graph_db

    db = get_graph_db()
    with db.session_for_kb("my-kb-id") as session:
        node = db.create_node(session, node_data, "my-kb-id")
"""

from typing import Optional
from enum import Enum

from memexia_backend.config import settings
from .base import GraphDatabaseBackend

# Lazy imports for optional backends
_graph_db: Optional[GraphDatabaseBackend] = None


class GraphDBType(str, Enum):
    """Supported graph database types."""
    KUZU = "kuzu"
    NEBULA = "nebula"


def get_graph_db() -> GraphDatabaseBackend:
    """
    Get the configured graph database backend.

    Returns:
        GraphDatabaseBackend instance
    """
    global _graph_db

    if _graph_db is not None:
        return _graph_db

    db_type = getattr(settings, 'GRAPH_DB_TYPE', 'kuzu').lower()

    if db_type == GraphDBType.NEBULA.value:
        from .nebula_backend import NebulaGraphDatabase

        host = getattr(settings, 'NEBULA_HOST', '127.0.0.1')
        port = getattr(settings, 'NEBULA_PORT', 9669)
        user = getattr(settings, 'NEBULA_USER', 'root')
        password = getattr(settings, 'NEBULA_PASSWORD', 'nebula')

        _graph_db = NebulaGraphDatabase(
            host=host,
            port=port,
            user=user,
            password=password,
        )
    else:
        # Default to Kuzu
        from .kuzu_backend import KuzuGraphDatabase

        _graph_db = KuzuGraphDatabase(
            base_path=getattr(settings, 'KUZU_DB_PATH', './data/kuzu_db')
        )

    _graph_db.initialize()
    return _graph_db


def close_graph_db() -> None:
    """Close the graph database connection."""
    global _graph_db

    if _graph_db is not None:
        _graph_db.close()
        _graph_db = None


__all__ = [
    "GraphDatabaseBackend",
    "GraphDBType",
    "get_graph_db",
    "close_graph_db",
]
