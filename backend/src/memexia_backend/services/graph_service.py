"""
Graph service for NebulaGraph and ChromaDB operations.

Each knowledge base has its own NebulaGraph Space, providing natural data isolation.
Uses nGQL (NebulaGraph Query Language) for graph operations.
"""

import uuid
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from nebula3.gclient.net.Session import Session as NebulaSession
from nebula3.data.ResultSet import ResultSet
from chromadb.api.models.Collection import Collection

from memexia_backend.schemas import (
    NodeCreate,
    NodeUpdate,
    EdgeCreate,
    Node,
    Edge,
    GraphData,
)
from memexia_backend.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)


def _escape_string(s: str) -> str:
    """Escape string for nGQL query."""
    if s is None:
        return ""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("'", "\\'")


def _parse_result_to_dict(result: ResultSet) -> List[Dict[str, Any]]:
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
            # Convert nebula values to Python types
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
            elif value.is_vertex():
                vertex = value.as_node()
                row_data[col_name] = {
                    "vid": vertex.get_id().as_string(),
                    "tags": [tag for tag in vertex.tags()],
                    "props": {
                        prop: vertex.properties(vertex.tags()[0]).get(prop)
                        for prop in vertex.prop_names(vertex.tags()[0])
                    }
                    if vertex.tags()
                    else {},
                }
            elif value.is_edge():
                edge = value.as_relationship()
                row_data[col_name] = {
                    "src": edge.start_vertex_id().as_string(),
                    "dst": edge.end_vertex_id().as_string(),
                    "type": edge.edge_name(),
                    "props": edge.properties(),
                }
            else:
                row_data[col_name] = str(value)
        rows.append(row_data)

    return rows


def create_node(
    session: NebulaSession,
    collection: Collection,
    node: NodeCreate,
    knowledge_base_id: str,
) -> Node:
    """
    Create a new node in the current space (knowledge base).

    Args:
        session: NebulaGraph session (already switched to correct space)
        collection: ChromaDB collection
        node: Node creation data
        knowledge_base_id: Knowledge base ID (for ChromaDB metadata)

    Returns:
        Created Node instance
    """
    node_id = str(uuid.uuid4())
    now = datetime.now().isoformat()

    # Escape strings for nGQL
    content_escaped = _escape_string(node.content)
    node_type_escaped = _escape_string(node.node_type)
    now_escaped = _escape_string(now)

    # Create vertex in NebulaGraph (no knowledge_base_id needed - space provides isolation)
    query = f'''
    INSERT VERTEX Node(content, node_type, created_at, updated_at)
    VALUES "{node_id}":("{content_escaped}", "{node_type_escaped}", "{now_escaped}", "{now_escaped}");
    '''

    result = session.execute(query)
    if not result.is_succeeded():
        raise RuntimeError(f"Failed to create node: {result.error_msg()}")

    created_node = Node(
        id=node_id,
        content=node.content,
        node_type=node.node_type,
        created_at=datetime.fromisoformat(now),
        updated_at=datetime.fromisoformat(now),
    )

    # Embed and store in ChromaDB with knowledge_base_id in metadata (for filtering)
    embedding = embedding_service.generate_embedding(node.content)
    collection.add(
        ids=[node_id],
        embeddings=[embedding],
        metadatas=[
            {
                "content": node.content,
                "type": node.node_type,
                "knowledge_base_id": knowledge_base_id,
            }
        ],
    )

    # Find similar nodes within the same knowledge base and create edges
    kb_node_count = collection.count()

    if kb_node_count > 1:
        results = collection.query(
            query_embeddings=[embedding],
            n_results=min(4, kb_node_count),  # Top 3 similar + self
            where={"knowledge_base_id": knowledge_base_id},
            include=["metadatas", "distances"],
        )

        similar_ids = results["ids"][0]
        if not results["distances"]:
            raise RuntimeError("No distances returned from ChromaDB query")
        distances = results["distances"][0]

        for i, target_id in enumerate(similar_ids):
            if target_id == node_id:
                continue

            # Chroma default is L2 (Squared Euclidean). Lower is closer.
            if distances[i] < 1.5:
                create_edge(
                    session,
                    EdgeCreate(
                        source_id=node_id,
                        target_id=target_id,
                        relation_type="SEMANTIC_RELATED",
                        weight=int((2.0 - distances[i]) * 10),
                    ),
                )

    logger.info(f"Created node {node_id} in knowledge base {knowledge_base_id}")
    return created_node


def get_node(
    session: NebulaSession,
    node_id: str,
) -> Optional[Node]:
    """
    Get a node by ID from the current space.

    Args:
        session: NebulaGraph session (already switched to correct space)
        node_id: Node ID

    Returns:
        Node if found, None otherwise
    """
    node_id_escaped = _escape_string(node_id)

    # Fetch node properties
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
    session: NebulaSession,
    node_id: str,
    node: NodeUpdate,
) -> Optional[Node]:
    """
    Update a node in the current space.

    Args:
        session: NebulaGraph session (already switched to correct space)
        node_id: Node ID
        node: Node update data

    Returns:
        Updated Node if found, None otherwise
    """
    # First verify the node exists
    existing_node = get_node(session, node_id)
    if existing_node is None:
        return None

    node_id_escaped = _escape_string(node_id)
    now = datetime.now().isoformat()
    now_escaped = _escape_string(now)

    # Build SET clause
    set_clauses = [f'updated_at = "{now_escaped}"']

    if node.content is not None:
        content_escaped = _escape_string(node.content)
        set_clauses.append(f'content = "{content_escaped}"')

    if node.node_type is not None:
        node_type_escaped = _escape_string(node.node_type)
        set_clauses.append(f'node_type = "{node_type_escaped}"')

    set_clause = ", ".join(set_clauses)

    # Update vertex in NebulaGraph
    query = f'''
    UPDATE VERTEX ON Node "{node_id_escaped}"
    SET {set_clause};
    '''

    result = session.execute(query)
    if not result.is_succeeded():
        logger.error(f"Failed to update node: {result.error_msg()}")
        return None

    # Return updated node
    return get_node(session, node_id)


def delete_node(
    session: NebulaSession,
    collection: Collection,
    node_id: str,
) -> bool:
    """
    Delete a node and its edges from the current space.

    Args:
        session: NebulaGraph session (already switched to correct space)
        collection: ChromaDB collection
        node_id: Node ID

    Returns:
        True if deleted, False if not found
    """
    # First verify the node exists
    existing_node = get_node(session, node_id)
    if existing_node is None:
        return False

    node_id_escaped = _escape_string(node_id)

    # Delete vertex with all connected edges
    query = f'DELETE VERTEX "{node_id_escaped}" WITH EDGE;'

    result = session.execute(query)
    if not result.is_succeeded():
        logger.error(f"Failed to delete node: {result.error_msg()}")
        return False

    # Delete from ChromaDB
    try:
        collection.delete(ids=[node_id])
    except Exception as e:
        logger.warning(f"Failed to delete node {node_id} from ChromaDB: {e}")

    logger.info(f"Deleted node {node_id}")
    return True


def create_edge(
    session: NebulaSession,
    edge: EdgeCreate,
) -> Optional[Edge]:
    """
    Create an edge between nodes in the current space.

    Args:
        session: NebulaGraph session (already switched to correct space)
        edge: Edge creation data

    Returns:
        Created Edge if successful, None otherwise
    """
    # Verify both nodes exist
    source_node = get_node(session, edge.source_id)
    target_node = get_node(session, edge.target_id)

    if source_node is None or target_node is None:
        logger.warning("Cannot create edge: source or target node not found")
        return None

    source_id_escaped = _escape_string(edge.source_id)
    target_id_escaped = _escape_string(edge.target_id)
    relation_type_escaped = _escape_string(edge.relation_type)
    weight = edge.weight if edge.weight is not None else 0

    # Insert edge in NebulaGraph
    query = f'''
    INSERT EDGE RELATED(relation_type, weight)
    VALUES "{source_id_escaped}"->"{target_id_escaped}":("{relation_type_escaped}", {weight});
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


def get_graph_data(session: NebulaSession) -> GraphData:
    """
    Get all graph data from the current space.

    Args:
        session: NebulaGraph session (already switched to correct space)

    Returns:
        GraphData with 'nodes' and 'edges' lists
    """
    # Get all nodes using MATCH (more reliable than LOOKUP for all nodes)
    nodes_query = """
    MATCH (n:Node)
    RETURN id(n) as vid,
           n.Node.content as content,
           n.Node.node_type as node_type,
           n.Node.created_at as created_at,
           n.Node.updated_at as updated_at;
    """

    nodes_result = session.execute(nodes_query)
    nodes_rows = _parse_result_to_dict(nodes_result)

    nodes = []
    node_ids = []

    for row in nodes_rows:
        node = Node(
            id=row.get("vid", ""),
            content=row.get("content", ""),
            node_type=row.get("node_type", ""),
            created_at=row.get("created_at", ""),
            updated_at=row.get("updated_at", ""),
        )
        nodes.append(node)
        node_ids.append(row.get("vid", ""))

    # Get all edges
    edges = []

    if node_ids:
        edges_query = """
        MATCH (a:Node)-[r:RELATED]->(b:Node)
        RETURN id(a) as source_id,
               id(b) as target_id,
               r.relation_type as relation_type,
               r.weight as weight;
        """

        edges_result = session.execute(edges_query)
        edges_rows = _parse_result_to_dict(edges_result)

        for row in edges_rows:
            edge = Edge(
                id=f"{row.get('source_id')}->{row.get('target_id')}",
                source_id=row.get("source_id", ""),
                target_id=row.get("target_id", ""),
                relation_type=row.get("relation_type", ""),
                weight=row.get("weight", 0),
            )
            edges.append(edge)

    return GraphData(nodes=nodes, edges=edges)


def delete_all_nodes(
    session: NebulaSession,
    collection: Collection,
    knowledge_base_id: str,
) -> int:
    """
    Delete all nodes and edges from the current space.

    Args:
        session: NebulaGraph session (already switched to correct space)
        collection: ChromaDB collection
        knowledge_base_id: Knowledge base ID (for ChromaDB cleanup)

    Returns:
        Number of nodes deleted
    """
    # Get all node IDs first for ChromaDB deletion
    ids_query = """
    MATCH (n:Node)
    RETURN id(n) as vid;
    """

    ids_result = session.execute(ids_query)
    ids_rows = _parse_result_to_dict(ids_result)
    node_ids = [row.get("vid", "") for row in ids_rows if row.get("vid")]

    deleted_count = len(node_ids)

    # Delete all vertices (with edges) from NebulaGraph
    if node_ids:
        node_ids_str = ", ".join([f'"{_escape_string(nid)}"' for nid in node_ids])
        delete_query = f"DELETE VERTEX {node_ids_str} WITH EDGE;"

        result = session.execute(delete_query)
        if not result.is_succeeded():
            logger.error(f"Failed to delete nodes: {result.error_msg()}")

        # Delete from ChromaDB
        try:
            collection.delete(ids=node_ids)
        except Exception as e:
            logger.warning(
                f"Failed to delete nodes from ChromaDB for KB {knowledge_base_id}: {e}"
            )

    logger.info(
        f"Deleted {deleted_count} nodes from knowledge base {knowledge_base_id}"
    )
    return deleted_count
