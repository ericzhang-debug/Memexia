"""
Kuzu graph database backend implementation.

Kuzu is an embedded graph database that uses Cypher query language.
Each knowledge base gets its own database directory for isolation.
"""

import uuid
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Any
from contextlib import contextmanager

import kuzu

from memexia_backend.config import settings
from memexia_backend.schemas import (
    Node,
    NodeCreate,
    NodeUpdate,
    Edge,
    EdgeCreate,
    GraphData,
)
from .base import GraphDatabaseBackend
from memexia_backend.logger import logger


class KuzuGraphDatabase(GraphDatabaseBackend):
    """
    Kuzu embedded graph database backend.

    Each knowledge base has its own database directory for complete isolation.
    Uses Cypher query language.
    """

    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize Kuzu backend.

        Args:
            base_path: Base directory for database storage
        """
        self.base_path = Path(base_path or settings.KUZU_DB_PATH)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._databases: dict[str, kuzu.Database] = {}
        self._connections: dict[str, kuzu.Connection] = {}
        logger.info(f"Kuzu backend initialized at {self.base_path}")

    def initialize(self) -> None:
        """Initialize the backend (no-op for Kuzu, DBs created on demand)."""
        pass

    def close(self) -> None:
        """Close all database connections."""
        for conn in self._connections.values():
            try:
                conn.close()
            except Exception:
                pass
        self._connections.clear()
        self._databases.clear()
        logger.info("Kuzu connections closed")

    def _kb_id_to_db_name(self, knowledge_base_id: str) -> str:
        """Convert KB ID to safe directory name."""
        safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', knowledge_base_id)
        return f"kb_{safe_name}"

    def _get_or_create_db(self, knowledge_base_id: str) -> tuple[kuzu.Database, kuzu.Connection]:
        """Get or create database and connection for a knowledge base."""
        db_name = self._kb_id_to_db_name(knowledge_base_id)

        if db_name not in self._databases:
            db_path = self.base_path / db_name
            db_path.mkdir(parents=True, exist_ok=True)

            # Create database
            db = kuzu.Database(str(db_path))
            conn = kuzu.Connection(db)

            # Initialize schema
            self._init_schema(conn)

            self._databases[db_name] = db
            self._connections[db_name] = conn
            logger.info(f"Created Kuzu database for KB {knowledge_base_id}")

        return self._databases[db_name], self._connections[db_name]

    def _init_schema(self, conn: kuzu.Connection) -> None:
        """Initialize database schema if not exists."""
        try:
            # Create Node table
            conn.execute("""
                CREATE NODE TABLE IF NOT EXISTS Node (
                    id STRING,
                    content STRING,
                    node_type STRING,
                    created_at STRING,
                    updated_at STRING,
                    PRIMARY KEY (id)
                )
            """)

            # Create RELATED edge table
            conn.execute("""
                CREATE REL TABLE IF NOT EXISTS RELATED (
                    FROM Node TO Node,
                    relation_type STRING,
                    weight INT64
                )
            """)

            logger.debug("Kuzu schema initialized")
        except Exception as e:
            # Schema might already exist
            logger.debug(f"Schema init note: {e}")

    @contextmanager
    def session_for_kb(self, knowledge_base_id: str):
        """
        Get a connection for a specific knowledge base.

        Args:
            knowledge_base_id: Knowledge base ID

        Yields:
            Kuzu Connection
        """
        _, conn = self._get_or_create_db(knowledge_base_id)
        yield conn

    def create_node(
        self,
        session: kuzu.Connection,
        node: NodeCreate,
        knowledge_base_id: str,
    ) -> Node:
        """Create a new node."""
        node_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        query = """
            CREATE (n:Node {
                id: $id,
                content: $content,
                node_type: $node_type,
                created_at: $created_at,
                updated_at: $updated_at
            })
        """

        session.execute(query, {
            "id": node_id,
            "content": node.content,
            "node_type": node.node_type,
            "created_at": now,
            "updated_at": now,
        })

        logger.info(f"Created node {node_id} in KB {knowledge_base_id}")

        return Node(
            id=node_id,
            content=node.content,
            node_type=node.node_type,
            created_at=datetime.fromisoformat(now),
            updated_at=datetime.fromisoformat(now),
        )

    def get_node(
        self,
        session: kuzu.Connection,
        node_id: str,
    ) -> Optional[Node]:
        """Get a node by ID."""
        query = """
            MATCH (n:Node {id: $id})
            RETURN n.id, n.content, n.node_type, n.created_at, n.updated_at
        """

        result = session.execute(query, {"id": node_id})

        # Support both driver Result objects and lists/tuples of rows
        row = None
        if isinstance(result, kuzu.QueryResult) and hasattr(result, "has_next"):
            if result.has_next():
                row = result.get_next()
        elif isinstance(result, (list, tuple)) and len(result) > 0:
            first = result[0]
            if hasattr(first, "has_next"):
                if first.has_next():
                    row = first.get_next()
        
        if not row:
            logger.warning(f"Node {node_id} not found")
            return None


        if row is not None:
            return Node(
                id=row[0],
                content=row[1],
                node_type=row[2],
                created_at=row[3],
                updated_at=row[4],
            )

        return None

    def update_node(
        self,
        session: kuzu.Connection,
        node_id: str,
        node: NodeUpdate,
    ) -> Optional[Node]:
        """Update a node."""
        # Check if exists
        existing = self.get_node(session, node_id)
        if existing is None:
            return None

        now = datetime.now().isoformat()

        # Build SET clause dynamically
        set_parts = ["n.updated_at = $updated_at"]
        params = {"id": node_id, "updated_at": now}

        if node.content is not None:
            set_parts.append("n.content = $content")
            params["content"] = node.content

        if node.node_type is not None:
            set_parts.append("n.node_type = $node_type")
            params["node_type"] = node.node_type

        set_clause = ", ".join(set_parts)
        query = f"""
            MATCH (n:Node {{id: $id}})
            SET {set_clause}
        """

        session.execute(query, params)

        return self.get_node(session, node_id)

    def delete_node(
        self,
        session: kuzu.Connection,
        node_id: str,
    ) -> bool:
        """Delete a node and its edges."""
        # Check if exists
        existing = self.get_node(session, node_id)
        if existing is None:
            return False

        # Delete edges first, then node
        session.execute("""
            MATCH (n:Node {id: $id})-[r]-()
            DELETE r
        """, {"id": node_id})

        session.execute("""
            MATCH (n:Node {id: $id})
            DELETE n
        """, {"id": node_id})

        logger.info(f"Deleted node {node_id}")
        return True

    def create_edge(
        self,
        session: kuzu.Connection,
        edge: EdgeCreate,
    ) -> Optional[Edge]:
        """Create an edge between nodes."""
        # Verify both nodes exist
        source = self.get_node(session, edge.source_id)
        target = self.get_node(session, edge.target_id)

        if source is None or target is None:
            logger.warning("Cannot create edge: source or target not found")
            return None

        weight = edge.weight if edge.weight is not None else 0

        query = """
            MATCH (a:Node {id: $source_id}), (b:Node {id: $target_id})
            CREATE (a)-[r:RELATED {relation_type: $relation_type, weight: $weight}]->(b)
        """

        session.execute(query, {
            "source_id": edge.source_id,
            "target_id": edge.target_id,
            "relation_type": edge.relation_type,
            "weight": weight,
        })

        return Edge(
            id=f"{edge.source_id}->{edge.target_id}",
            source_id=edge.source_id,
            target_id=edge.target_id,
            relation_type=edge.relation_type,
            weight=weight,
        )

    def get_graph_data(
        self,
        session: kuzu.Connection,
    ) -> GraphData:
        """Get all nodes and edges."""
        # Get all nodes
        nodes_result = session.execute("""
            MATCH (n:Node)
            RETURN n.id, n.content, n.node_type, n.created_at, n.updated_at
        """)

        nodes = []

        def _iter_result(res):
            # Yield rows from either Result-like objects or lists/tuples
            if isinstance(res, kuzu.QueryResult) and hasattr(res, "has_next"):
                while res.has_next():
                    yield res.get_next()
            elif isinstance(res, (list, tuple)):
                for item in res:
                    if hasattr(item, "has_next"):
                        while item.has_next():
                            yield item.get_next()
                    else:
                        yield item

        def _normalize_row(row):
            # Normalize row to a list of values so numeric indexing is safe
            if row is None:
                return []
            if isinstance(row, dict):
                return list(row.values())
            try:
                if isinstance(row, (list, tuple)):
                    return list(row)
                # Some driver row types are iterable
                return list(row)
            except Exception:
                return [row]

        for row in _iter_result(nodes_result):
            vals = _normalize_row(row)
            nodes.append(Node(
                id=vals[0] if len(vals) > 0 else None,
                content=vals[1] if len(vals) > 1 else None,
                node_type=vals[2] if len(vals) > 2 else None,
                created_at=vals[3] if len(vals) > 3 else None,
                updated_at=vals[4] if len(vals) > 4 else None,
            ))

        # Get all edges
        edges_result = session.execute("""
            MATCH (a:Node)-[r:RELATED]->(b:Node)
            RETURN a.id, b.id, r.relation_type, r.weight
        """)

        edges = []

        def _iter_result(res):
            # Yield rows from either Result-like objects or lists/tuples
            if hasattr(res, "has_next"):
                while res.has_next():
                    yield res.get_next()
            elif isinstance(res, (list, tuple)):
                for item in res:
                    if hasattr(item, "has_next"):
                        while item.has_next():
                            yield item.get_next()
                    else:
                        yield item

        for row in _iter_result(edges_result):
            vals = _normalize_row(row)
            edges.append(Edge(
                id=f"{vals[0]}->{vals[1]}" if len(vals) > 1 else "",
                source_id=vals[0] if len(vals) > 0 else None,
                target_id=vals[1] if len(vals) > 1 else None,
                relation_type=vals[2] if len(vals) > 2 else None,
                weight=(vals[3] or 0) if len(vals) > 3 else 0,
            ))

        return GraphData(nodes=nodes, edges=edges)

    def delete_all_nodes(
        self,
        session: kuzu.Connection,
    ) -> int:
        """Delete all nodes and edges."""
        # Count nodes first
        count_result = session.execute("MATCH (n:Node) RETURN count(n)")
        count = 0

        def _get_first_from_row(row: Any) -> int:
            # Handle None
            if row is None:
                return 0
            # If row is a plain tuple/list
            if isinstance(row, (list, tuple)):
                return int(row[0]) if len(row) > 0 else 0
            # If row is a mapping/dict-like
            if isinstance(row, dict):
                vals = list(row.values())
                return int(vals[0]) if vals else 0
            # If row is a driver result/row object that exposes get_next()
            if hasattr(row, "get_next"):
                try:
                    next_row = row.get_next()
                except Exception:
                    return 0
                return _get_first_from_row(next_row)
            # Fallback: try indexing or casting
            try:
                return int(row[0])
            except Exception:
                try:
                    return int(row)
                except Exception:
                    return 0

        if isinstance(count_result, kuzu.QueryResult) and hasattr(count_result, "has_next"):
            if count_result.has_next():
                count = _get_first_from_row(count_result.get_next())
        elif isinstance(count_result, (list, tuple)) and len(count_result) > 0:
            first = count_result[0]
            if isinstance(first, kuzu.QueryResult) and hasattr(first, "has_next"):
                if first.has_next():
                    count = _get_first_from_row(first.get_next())
            else:
                count = _get_first_from_row(first)

        # Delete all edges
        session.execute("MATCH ()-[r:RELATED]->() DELETE r")

        # Delete all nodes
        session.execute("MATCH (n:Node) DELETE n")

        logger.info(f"Deleted {count} nodes")
        return count

    def delete_kb_data(
        self,
        knowledge_base_id: str,
    ) -> bool:
        """Delete all data for a knowledge base (drop the database)."""
        import shutil

        db_name = self._kb_id_to_db_name(knowledge_base_id)
        db_path = self.base_path / db_name

        # Close connection if open
        if db_name in self._connections:
            try:
                self._connections[db_name].close()
            except Exception:
                pass
            del self._connections[db_name]

        if db_name in self._databases:
            del self._databases[db_name]

        # Remove directory
        if db_path.exists():
            shutil.rmtree(db_path)
            logger.info(f"Deleted database for KB {knowledge_base_id}")
            return True

        return False
