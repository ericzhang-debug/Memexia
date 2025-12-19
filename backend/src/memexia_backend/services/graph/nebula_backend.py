"""
NebulaGraph database backend implementation.

NebulaGraph is a distributed graph database that uses nGQL query language.
Each knowledge base gets its own Space for isolation.
"""

import uuid
import re
import time
from typing import Optional, Any, Dict, List
from contextlib import contextmanager

# from memexia_backend.config import settings
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

# Optional import - only available if nebula3-python is installed
try:
    from nebula3.gclient.net import ConnectionPool
    from nebula3.Config import Config as NebulaConfig
    # from nebula3.gclient.net.Session import Session as NebulaSession
    # from nebula3.data.ResultSet import ResultSet
    NEBULA_AVAILABLE = True
except ImportError:
    NEBULA_AVAILABLE = False
    logger.warning("nebula3-python not installed, NebulaGraph backend unavailable")


def _escape_string(s: str) -> str:
    """Escape string for nGQL query."""
    if s is None:
        return ""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("'", "\\'")


def _parse_result_to_dict(result) -> List[Dict[str, Any]]:
    """Parse NebulaGraph result set to list of dictionaries."""
    if not result.is_succeeded():
        logger.error(f"Query failed: {result.error_msg()}")
        return []

    rows = []
    if result.is_empty():
        return rows

    col_names = result.keys()

    for row_idx in range(result.row_size()):
        row_data = {}
        for col_idx, col_name in enumerate(col_names):
            value = result.row_values(row_idx)[col_idx]
            if value.is_null():
                row_data[col_name] = None
            elif value.is_string():
                row_data[col_name] = value.as_string()
            elif value.is_int():
                row_data[col_name] = value.as_int()
            elif value.is_double():
                row_data[col_name] = value.as_double()
            elif value.is_bool():
                row_data[col_name] = value.as_bool()
            else:
                row_data[col_name] = str(value)
        rows.append(row_data)

    return rows


class NebulaGraphDatabase(GraphDatabaseBackend):
    """
    NebulaGraph distributed graph database backend.

    Each knowledge base has its own Space for complete isolation.
    Uses nGQL query language.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 9669,
        user: str = "root",
        password: str = "nebula",
    ):
        """
        Initialize NebulaGraph backend.

        Args:
            host: NebulaGraph host
            port: NebulaGraph port
            user: Username
            password: Password
        """
        if not NEBULA_AVAILABLE:
            raise RuntimeError("nebula3-python is not installed")

        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self._pool: Optional[ConnectionPool] = None # type: ignore
        self._initialized_spaces: set[str] = set()

    def initialize(self) -> None:
        """Initialize the connection pool."""
        if self._pool is not None:
            return

        config = NebulaConfig() # type: ignore
        config.max_connection_pool_size = 10
        config.timeout = 5000

        self._pool = ConnectionPool() # type: ignore
        ok = self._pool.init([(self.host, self.port)], config)

        if not ok:
            raise RuntimeError("Failed to initialize NebulaGraph connection pool")

        logger.info("NebulaGraph connection pool initialized")

    def close(self) -> None:
        """Close the connection pool."""
        if self._pool is not None:
            self._pool.close()
            self._pool = None
            self._initialized_spaces.clear()
            logger.info("NebulaGraph connection pool closed")

    def _kb_id_to_space_name(self, knowledge_base_id: str) -> str:
        """Convert KB ID to valid space name."""
        safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', knowledge_base_id)
        return f"kb_{safe_name}"

    def _ensure_space_exists(self, knowledge_base_id: str) -> None:
        """Ensure space exists for a knowledge base."""
        space_name = self._kb_id_to_space_name(knowledge_base_id)

        if space_name in self._initialized_spaces:
            return
        
        if self._pool is None:
            raise RuntimeError("Connection pool not initialized")
        
        session = self._pool.get_session(self.user, self.password)

        try:
            # Create space
            session.execute(f"""
                CREATE SPACE IF NOT EXISTS `{space_name}` (
                    partition_num=10,
                    replica_factor=1,
                    vid_type=FIXED_STRING(64)
                );
            """)

            time.sleep(2)
            session.execute(f"USE `{space_name}`;")

            # Create schema
            session.execute("""
                CREATE TAG IF NOT EXISTS Node (
                    content string,
                    node_type string,
                    created_at string,
                    updated_at string
                );
            """)

            session.execute("""
                CREATE EDGE IF NOT EXISTS RELATED (
                    relation_type string,
                    weight int
                );
            """)

            time.sleep(1)

            self._initialized_spaces.add(space_name)
            logger.info(f"NebulaGraph space '{space_name}' initialized")

        finally:
            session.release()

    @contextmanager
    def session_for_kb(self, knowledge_base_id: str):
        """Get a session for a specific knowledge base."""
        if self._pool is None:
            self.initialize()

        self._ensure_space_exists(knowledge_base_id)

        space_name = self._kb_id_to_space_name(knowledge_base_id)
        if self._pool is None:
            raise RuntimeError("Connection pool not initialized")
        session = self._pool.get_session(self.user, self.password)

        try:
            session.execute(f"USE `{space_name}`;")
            yield session
        finally:
            session.release()

    def create_node(
        self,
        session: Any,
        node: NodeCreate,
        knowledge_base_id: str,
    ) -> Node:
        """Create a new node."""
        from datetime import datetime

        node_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        content_escaped = _escape_string(node.content)
        node_type_escaped = _escape_string(node.node_type)
        now_escaped = _escape_string(now)

        query = f'''
        INSERT VERTEX Node(content, node_type, created_at, updated_at)
        VALUES "{node_id}":("{content_escaped}", "{node_type_escaped}", "{now_escaped}", "{now_escaped}");
        '''

        result = session.execute(query)
        if not result.is_succeeded():
            raise RuntimeError(f"Failed to create node: {result.error_msg()}")

        logger.info(f"Created node {node_id}")

        return Node(
            id=node_id,
            content=node.content,
            node_type=node.node_type,
            created_at=datetime.fromisoformat(now),
            updated_at=datetime.fromisoformat(now),
        )

    def get_node(
        self,
        session: Any,
        node_id: str,
    ) -> Optional[Node]:
        """Get a node by ID."""
        node_id_escaped = _escape_string(node_id)

        query = f'''
        FETCH PROP ON Node "{node_id_escaped}"
        YIELD id(vertex) as vid,
              properties(vertex).content as content,
              properties(vertex).node_type as node_type,
              properties(vertex).created_at as created_at,
              properties(vertex).updated_at as updated_at;
        '''

        result = session.execute(query)
        rows = _parse_result_to_dict(result)

        if not rows:
            return None

        row = rows[0]
        return Node(
            id=row.get("vid", node_id),
            content=row.get("content", ""),
            node_type=row.get("node_type", ""),
            created_at=row.get("created_at", ""),
            updated_at=row.get("updated_at", ""),
        )

    def update_node(
        self,
        session: Any,
        node_id: str,
        node: NodeUpdate,
    ) -> Optional[Node]:
        """Update a node."""
        from datetime import datetime

        existing = self.get_node(session, node_id)
        if existing is None:
            return None

        node_id_escaped = _escape_string(node_id)
        now = datetime.now().isoformat()
        now_escaped = _escape_string(now)

        set_clauses = [f'updated_at = "{now_escaped}"']

        if node.content is not None:
            set_clauses.append(f'content = "{_escape_string(node.content)}"')

        if node.node_type is not None:
            set_clauses.append(f'node_type = "{_escape_string(node.node_type)}"')

        set_clause = ", ".join(set_clauses)

        query = f'''
        UPDATE VERTEX ON Node "{node_id_escaped}"
        SET {set_clause};
        '''

        result = session.execute(query)
        if not result.is_succeeded():
            logger.error(f"Failed to update node: {result.error_msg()}")
            return None

        return self.get_node(session, node_id)

    def delete_node(
        self,
        session: Any,
        node_id: str,
    ) -> bool:
        """Delete a node and its edges."""
        existing = self.get_node(session, node_id)
        if existing is None:
            return False

        node_id_escaped = _escape_string(node_id)

        query = f'DELETE VERTEX "{node_id_escaped}" WITH EDGE;'

        result = session.execute(query)
        if not result.is_succeeded():
            logger.error(f"Failed to delete node: {result.error_msg()}")
            return False

        logger.info(f"Deleted node {node_id}")
        return True

    def create_edge(
        self,
        session: Any,
        edge: EdgeCreate,
    ) -> Optional[Edge]:
        """Create an edge between nodes."""
        source = self.get_node(session, edge.source_id)
        target = self.get_node(session, edge.target_id)

        if source is None or target is None:
            logger.warning("Cannot create edge: source or target not found")
            return None

        source_escaped = _escape_string(edge.source_id)
        target_escaped = _escape_string(edge.target_id)
        relation_escaped = _escape_string(edge.relation_type)
        weight = edge.weight if edge.weight is not None else 0

        query = f'''
        INSERT EDGE RELATED(relation_type, weight)
        VALUES "{source_escaped}"->"{target_escaped}":("{relation_escaped}", {weight});
        '''

        result = session.execute(query)
        if not result.is_succeeded():
            logger.error(f"Failed to create edge: {result.error_msg()}")
            return None

        return Edge(
            id=f"{edge.source_id}->{edge.target_id}",
            source_id=edge.source_id,
            target_id=edge.target_id,
            relation_type=edge.relation_type,
            weight=weight,
        )

    def get_graph_data(
        self,
        session: Any,
    ) -> GraphData:
        """Get all nodes and edges."""
        # Get nodes
        nodes_query = '''
        MATCH (n:Node)
        RETURN id(n) as vid,
               n.Node.content as content,
               n.Node.node_type as node_type,
               n.Node.created_at as created_at,
               n.Node.updated_at as updated_at;
        '''

        nodes_result = session.execute(nodes_query)
        nodes_rows = _parse_result_to_dict(nodes_result)

        nodes = []
        for row in nodes_rows:
            nodes.append(Node(
                id=row.get("vid", ""),
                content=row.get("content", ""),
                node_type=row.get("node_type", ""),
                created_at=row.get("created_at", ""),
                updated_at=row.get("updated_at", ""),
            ))

        # Get edges
        edges_query = '''
        MATCH (a:Node)-[r:RELATED]->(b:Node)
        RETURN id(a) as source_id,
               id(b) as target_id,
               r.relation_type as relation_type,
               r.weight as weight;
        '''

        edges_result = session.execute(edges_query)
        edges_rows = _parse_result_to_dict(edges_result)

        edges = []
        for row in edges_rows:
            edges.append(Edge(
                id=f"{row.get('source_id')}->{row.get('target_id')}",
                source_id=row.get("source_id", ""),
                target_id=row.get("target_id", ""),
                relation_type=row.get("relation_type", ""),
                weight=row.get("weight", 0),
            ))

        return GraphData(nodes=nodes, edges=edges)

    def delete_all_nodes(
        self,
        session: Any,
    ) -> int:
        """Delete all nodes and edges."""
        # Get count
        count_result = session.execute("MATCH (n:Node) RETURN id(n) as vid;")
        rows = _parse_result_to_dict(count_result)
        count = len(rows)

        if rows:
            ids_str = ", ".join([f'"{_escape_string(r["vid"])}"' for r in rows])
            session.execute(f"DELETE VERTEX {ids_str} WITH EDGE;")

        logger.info(f"Deleted {count} nodes")
        return count

    def delete_kb_data(
        self,
        knowledge_base_id: str,
    ) -> bool:
        """Delete all data for a knowledge base (drop the space)."""
        if self._pool is None:
            return False

        space_name = self._kb_id_to_space_name(knowledge_base_id)
        session = self._pool.get_session(self.user, self.password)

        try:
            result = session.execute(f"DROP SPACE IF EXISTS `{space_name}`;")
            if result.is_succeeded():
                self._initialized_spaces.discard(space_name)
                logger.info(f"Deleted space '{space_name}'")
                return True
            else:
                logger.error(f"Failed to delete space: {result.error_msg()}")
                return False
        finally:
            session.release()
