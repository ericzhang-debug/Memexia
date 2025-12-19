"""
Abstract base class for graph database backends.

This module defines the interface that all graph database backends must implement.
"""

from abc import ABC, abstractmethod
from typing import Optional, Any, ContextManager

from memexia_backend.schemas import (
    Node,
    NodeCreate,
    NodeUpdate,
    Edge,
    EdgeCreate,
    GraphData,
)


class GraphDatabaseBackend(ABC):
    """
    Abstract base class for graph database backends.

    All graph database implementations (Kuzu, NebulaGraph, Neo4j, etc.)
    must implement this interface.
    """

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the database connection and schema."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the database connection."""
        pass

    @abstractmethod
    def session_for_kb(self, knowledge_base_id: str) -> ContextManager[Any]:
        """
        Get a session/connection for a specific knowledge base.

        Args:
            knowledge_base_id: Knowledge base ID

        Returns:
            Context manager yielding a database session or connection
        """
        pass

    @abstractmethod
    def create_node(
        self,
        session: Any,
        node: NodeCreate,
        knowledge_base_id: str,
    ) -> Node:
        """
        Create a new node.

        Args:
            session: Database session
            node: Node creation data
            knowledge_base_id: Knowledge base ID

        Returns:
            Created Node
        """
        pass

    @abstractmethod
    def get_node(
        self,
        session: Any,
        node_id: str,
    ) -> Optional[Node]:
        """
        Get a node by ID.

        Args:
            session: Database session
            node_id: Node ID

        Returns:
            Node if found, None otherwise
        """
        pass

    @abstractmethod
    def update_node(
        self,
        session: Any,
        node_id: str,
        node: NodeUpdate,
    ) -> Optional[Node]:
        """
        Update a node.

        Args:
            session: Database session
            node_id: Node ID
            node: Update data

        Returns:
            Updated Node if found, None otherwise
        """
        pass

    @abstractmethod
    def delete_node(
        self,
        session: Any,
        node_id: str,
    ) -> bool:
        """
        Delete a node.

        Args:
            session: Database session
            node_id: Node ID

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    def create_edge(
        self,
        session: Any,
        edge: EdgeCreate,
    ) -> Optional[Edge]:
        """
        Create an edge between nodes.

        Args:
            session: Database session
            edge: Edge creation data

        Returns:
            Created Edge if successful, None otherwise
        """
        pass

    @abstractmethod
    def get_graph_data(
        self,
        session: Any,
    ) -> GraphData:
        """
        Get all nodes and edges.

        Args:
            session: Database session

        Returns:
            GraphData with nodes and edges
        """
        pass

    @abstractmethod
    def delete_all_nodes(
        self,
        session: Any,
    ) -> int:
        """
        Delete all nodes and edges.

        Args:
            session: Database session

        Returns:
            Number of nodes deleted
        """
        pass

    @abstractmethod
    def delete_kb_data(
        self,
        knowledge_base_id: str,
    ) -> bool:
        """
        Delete all data for a knowledge base.

        Args:
            knowledge_base_id: Knowledge base ID

        Returns:
            True if successful
        """
        pass
