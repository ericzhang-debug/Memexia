"""
Graph service for graph database and ChromaDB operations.

Uses pluggable graph database backend (Kuzu or NebulaGraph).
Each knowledge base has its own database/space for data isolation.
"""

from typing import Optional

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
from memexia_backend.services.graph import get_graph_db
from memexia_backend.logger import logger


def create_node(
    collection: Collection,
    node: NodeCreate,
    knowledge_base_id: str,
) -> Node:
    """
    Create a new node in the knowledge base.

    Args:
        collection: ChromaDB collection
        node: Node creation data
        knowledge_base_id: Knowledge base ID

    Returns:
        Created Node instance
    """
    db = get_graph_db()

    with db.session_for_kb(knowledge_base_id) as session:
        # Create node in graph database
        created_node = db.create_node(session, node, knowledge_base_id)

        # Embed and store in ChromaDB with knowledge_base_id in metadata
        embedding = embedding_service.generate_embedding(node.content)
        collection.add(
            ids=[created_node.id],
            embeddings=[embedding],
            metadatas=[
                {
                    "content": node.content,
                    "type": node.node_type,
                    "knowledge_base_id": knowledge_base_id,
                }
            ],
        )

        # Find similar nodes and create edges
        kb_node_count = collection.count()

        if kb_node_count > 1:
            results = collection.query(
                query_embeddings=[embedding],
                n_results=min(4, kb_node_count),
                where={"knowledge_base_id": knowledge_base_id},
                include=["metadatas", "distances"],
            )

            similar_ids = results["ids"][0]
            if results["distances"]:
                distances = results["distances"][0]

                for i, target_id in enumerate(similar_ids):
                    if target_id == created_node.id:
                        continue

                    # Lower distance = more similar (L2 distance)
                    if distances[i] < 1.5:
                        db.create_edge(
                            session,
                            EdgeCreate(
                                source_id=created_node.id,
                                target_id=target_id,
                                relation_type="SEMANTIC_RELATED",
                                weight=int((2.0 - distances[i]) * 10),
                            ),
                        )

        logger.info(f"Created node {created_node.id} in KB {knowledge_base_id}")
        return created_node


def get_node(
    node_id: str,
    knowledge_base_id: str,
) -> Optional[Node]:
    """
    Get a node by ID.

    Args:
        node_id: Node ID
        knowledge_base_id: Knowledge base ID

    Returns:
        Node if found, None otherwise
    """
    db = get_graph_db()

    with db.session_for_kb(knowledge_base_id) as session:
        return db.get_node(session, node_id)


def update_node(
    node_id: str,
    node: NodeUpdate,
    knowledge_base_id: str,
) -> Optional[Node]:
    """
    Update a node.

    Args:
        node_id: Node ID
        node: Node update data
        knowledge_base_id: Knowledge base ID

    Returns:
        Updated Node if found, None otherwise
    """
    db = get_graph_db()

    with db.session_for_kb(knowledge_base_id) as session:
        return db.update_node(session, node_id, node)


def delete_node(
    collection: Collection,
    node_id: str,
    knowledge_base_id: str,
) -> bool:
    """
    Delete a node and its edges.

    Args:
        collection: ChromaDB collection
        node_id: Node ID
        knowledge_base_id: Knowledge base ID

    Returns:
        True if deleted, False if not found
    """
    db = get_graph_db()

    with db.session_for_kb(knowledge_base_id) as session:
        deleted = db.delete_node(session, node_id)

        if deleted:
            # Also delete from ChromaDB
            try:
                collection.delete(ids=[node_id])
            except Exception as e:
                logger.warning(f"Failed to delete node {node_id} from ChromaDB: {e}")

        return deleted


def create_edge(
    edge: EdgeCreate,
    knowledge_base_id: str,
) -> Optional[Edge]:
    """
    Create an edge between nodes.

    Args:
        edge: Edge creation data
        knowledge_base_id: Knowledge base ID

    Returns:
        Created Edge if successful, None otherwise
    """
    db = get_graph_db()

    with db.session_for_kb(knowledge_base_id) as session:
        return db.create_edge(session, edge)


def get_graph_data(knowledge_base_id: str) -> GraphData:
    """
    Get all graph data for a knowledge base.

    Args:
        knowledge_base_id: Knowledge base ID

    Returns:
        GraphData with nodes and edges
    """
    db = get_graph_db()

    with db.session_for_kb(knowledge_base_id) as session:
        return db.get_graph_data(session)


def delete_all_nodes(
    collection: Collection,
    knowledge_base_id: str,
) -> int:
    """
    Delete all nodes and edges in a knowledge base.

    Args:
        collection: ChromaDB collection
        knowledge_base_id: Knowledge base ID

    Returns:
        Number of nodes deleted
    """
    db = get_graph_db()

    with db.session_for_kb(knowledge_base_id) as session:
        # Get all node IDs first for ChromaDB deletion
        graph_data = db.get_graph_data(session)
        node_ids = [node.id for node in graph_data.nodes]

        # Delete from graph database
        deleted_count = db.delete_all_nodes(session)

        # Delete from ChromaDB
        if node_ids:
            try:
                collection.delete(ids=node_ids)
            except Exception as e:
                logger.warning(f"Failed to delete nodes from ChromaDB: {e}")

        logger.info(f"Deleted {deleted_count} nodes from KB {knowledge_base_id}")
        return deleted_count


def delete_kb_data(knowledge_base_id: str) -> bool:
    """
    Delete all data for a knowledge base.

    Args:
        knowledge_base_id: Knowledge base ID

    Returns:
        True if successful
    """
    db = get_graph_db()
    return db.delete_kb_data(knowledge_base_id)
