"""
Graph service for Neo4j and ChromaDB operations with knowledge base isolation.

All operations are scoped to a specific knowledge base using the knowledge_base_id parameter.
"""

import uuid
import logging
from datetime import datetime
from typing import List, Optional
from neo4j import Session
from chromadb.api.models.Collection import Collection

from memexia_backend.schemas import NodeCreate, NodeUpdate, EdgeCreate, Node, Edge
from memexia_backend.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)


def _map_node(record) -> Node:
    """Map Neo4j record to Node schema."""
    data = dict(record)
    return Node(**data)


def _map_edge(record) -> Edge:
    """Map Neo4j record to Edge schema."""
    return Edge(**record)


def create_node(
    session: Session,
    collection: Collection,
    node: NodeCreate,
    knowledge_base_id: str,
) -> Node:
    """
    Create a new node in a knowledge base.

    Args:
        session: Neo4j session
        collection: ChromaDB collection
        node: Node creation data
        knowledge_base_id: Knowledge base ID for isolation

    Returns:
        Created Node instance
    """
    node_id = str(uuid.uuid4())
    now = datetime.now().isoformat()

    node_data = {
        "id": node_id,
        "content": node.content,
        "node_type": node.node_type,
        "knowledge_base_id": knowledge_base_id,
        "created_at": now,
        "updated_at": now,
    }

    # 1. Create in Neo4j with knowledge_base_id
    query = (
        "CREATE (n:Node {id: $id, content: $content, node_type: $node_type, "
        "knowledge_base_id: $knowledge_base_id, created_at: $created_at, updated_at: $updated_at}) "
        "RETURN n"
    )
    result = session.run(query, **node_data).single()
    created_node = _map_node(result["n"])

    # 2. Embed and store in ChromaDB with knowledge_base_id in metadata
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

    # 3. Find similar nodes within the same knowledge base and create edges
    # Filter by knowledge_base_id in the query
    kb_node_count = collection.count()

    if kb_node_count > 1:
        results = collection.query(
            query_embeddings=[embedding],
            n_results=min(4, kb_node_count),  # Top 3 similar + self
            where={"knowledge_base_id": knowledge_base_id},
            include=["metadatas", "distances"],
        )

        similar_ids = results["ids"][0]
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
                    knowledge_base_id,
                )

    logger.info(f"Created node {node_id} in knowledge base {knowledge_base_id}")
    return created_node


def get_node(
    session: Session,
    node_id: str,
    knowledge_base_id: str,
) -> Optional[Node]:
    """
    Get a node by ID within a knowledge base.

    Args:
        session: Neo4j session
        node_id: Node ID
        knowledge_base_id: Knowledge base ID for isolation

    Returns:
        Node if found, None otherwise
    """
    query = (
        "MATCH (n:Node {id: $node_id, knowledge_base_id: $knowledge_base_id}) "
        "RETURN n"
    )
    result = session.run(
        query, node_id=node_id, knowledge_base_id=knowledge_base_id
    ).single()

    if result:
        return _map_node(result["n"])
    return None


def update_node(
    session: Session,
    node_id: str,
    node: NodeUpdate,
    knowledge_base_id: str,
) -> Optional[Node]:
    """
    Update a node within a knowledge base.

    Args:
        session: Neo4j session
        node_id: Node ID
        node: Node update data
        knowledge_base_id: Knowledge base ID for isolation

    Returns:
        Updated Node if found, None otherwise
    """
    fields = []
    params = {
        "node_id": node_id,
        "knowledge_base_id": knowledge_base_id,
        "updated_at": datetime.now().isoformat(),
    }

    if node.content is not None:
        fields.append("n.content = $content")
        params["content"] = node.content
    if node.node_type is not None:
        fields.append("n.node_type = $node_type")
        params["node_type"] = node.node_type

    fields.append("n.updated_at = $updated_at")

    set_clause = ", ".join(fields)
    query = (
        f"MATCH (n:Node {{id: $node_id, knowledge_base_id: $knowledge_base_id}}) "
        f"SET {set_clause} RETURN n"
    )

    result = session.run(query, **params).single()
    if result:
        return _map_node(result["n"])
    return None


def delete_node(
    session: Session,
    collection: Collection,
    node_id: str,
    knowledge_base_id: str,
) -> bool:
    """
    Delete a node and its edges within a knowledge base.

    Args:
        session: Neo4j session
        collection: ChromaDB collection
        node_id: Node ID
        knowledge_base_id: Knowledge base ID for isolation

    Returns:
        True if deleted, False if not found
    """
    # Delete from Neo4j (with relationships)
    query = (
        "MATCH (n:Node {id: $node_id, knowledge_base_id: $knowledge_base_id}) "
        "DETACH DELETE n "
        "RETURN count(n) as deleted"
    )
    result = session.run(
        query, node_id=node_id, knowledge_base_id=knowledge_base_id
    ).single()

    if result and result["deleted"] > 0:
        # Delete from ChromaDB
        try:
            collection.delete(ids=[node_id])
        except Exception as e:
            logger.warning(f"Failed to delete node {node_id} from ChromaDB: {e}")

        logger.info(f"Deleted node {node_id} from knowledge base {knowledge_base_id}")
        return True

    return False


def create_edge(
    session: Session,
    edge: EdgeCreate,
    knowledge_base_id: str,
) -> Optional[Edge]:
    """
    Create an edge between nodes in a knowledge base.

    Args:
        session: Neo4j session
        edge: Edge creation data
        knowledge_base_id: Knowledge base ID for isolation

    Returns:
        Created Edge if successful, None otherwise
    """
    edge_id = str(uuid.uuid4())
    query = (
        "MATCH (a:Node {id: $source_id, knowledge_base_id: $knowledge_base_id}), "
        "(b:Node {id: $target_id, knowledge_base_id: $knowledge_base_id}) "
        "MERGE (a)-[r:RELATED {id: $id, type: $relation_type}]->(b) "
        "SET r.weight = $weight "
        "RETURN r, a.id as source_id, b.id as target_id"
    )
    params = edge.model_dump()
    params["id"] = edge_id
    params["knowledge_base_id"] = knowledge_base_id

    result = session.run(query, **params).single()
    if result:
        data = dict(result["r"])
        data["source_id"] = result["source_id"]
        data["target_id"] = result["target_id"]
        data["relation_type"] = data.get("type", edge.relation_type)
        return Edge(**data)
    return None


def get_graph_data(session: Session, knowledge_base_id: str) -> dict:
    """
    Get all graph data for a knowledge base.

    Args:
        session: Neo4j session
        knowledge_base_id: Knowledge base ID for isolation

    Returns:
        Dict with 'nodes' and 'edges' lists
    """
    # Get all nodes in the knowledge base
    nodes_query = (
        "MATCH (n:Node {knowledge_base_id: $knowledge_base_id}) " "RETURN n"
    )
    nodes_result = session.run(nodes_query, knowledge_base_id=knowledge_base_id)
    nodes = [_map_node(record["n"]) for record in nodes_result]

    # Get all edges within the knowledge base
    edges_query = (
        "MATCH (a:Node {knowledge_base_id: $knowledge_base_id})"
        "-[r]->"
        "(b:Node {knowledge_base_id: $knowledge_base_id}) "
        "RETURN r, a.id as source_id, b.id as target_id"
    )
    edges_result = session.run(edges_query, knowledge_base_id=knowledge_base_id)
    edges = []
    for record in edges_result:
        data = dict(record["r"])
        data["source_id"] = record["source_id"]
        data["target_id"] = record["target_id"]
        edges.append(Edge(**data))

    return {"nodes": nodes, "edges": edges}


def delete_all_nodes_in_kb(
    session: Session,
    collection: Collection,
    knowledge_base_id: str,
) -> int:
    """
    Delete all nodes and edges in a knowledge base.

    Args:
        session: Neo4j session
        collection: ChromaDB collection
        knowledge_base_id: Knowledge base ID

    Returns:
        Number of nodes deleted
    """
    # Get all node IDs first for ChromaDB deletion
    ids_query = (
        "MATCH (n:Node {knowledge_base_id: $knowledge_base_id}) " "RETURN n.id as id"
    )
    ids_result = session.run(ids_query, knowledge_base_id=knowledge_base_id)
    node_ids = [record["id"] for record in ids_result]

    # Delete from Neo4j
    delete_query = (
        "MATCH (n:Node {knowledge_base_id: $knowledge_base_id}) "
        "DETACH DELETE n "
        "RETURN count(n) as deleted"
    )
    result = session.run(delete_query, knowledge_base_id=knowledge_base_id).single()
    deleted_count = result["deleted"] if result else 0

    # Delete from ChromaDB
    if node_ids:
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
