"""
Node API routes with knowledge base isolation.

Each knowledge base has its own NebulaGraph Space for data isolation.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from chromadb.api.models.Collection import Collection
from sqlalchemy.orm import Session as SQLSession

from memexia_backend.database import (
    get_nebula_session_for_kb,
    get_chroma_collection,
    get_db,
)
from memexia_backend.schemas import (
    Node,
    NodeCreate,
    NodeUpdate,
    AIExpandRequest,
    GraphData,
)
from memexia_backend.services import graph_service, ai_service
from memexia_backend.services.knowledge_base_service import knowledge_base_service
from memexia_backend.models import User
from memexia_backend.routers.v1.auth import get_current_user

router = APIRouter(
    prefix="/api/v1/knowledge-bases/{kb_id}/nodes",
    tags=["nodes"],
    responses={404: {"description": "Not found"}},
)


def get_kb_with_access(
    kb_id: str,
    db: SQLSession,
    current_user: Optional[User],
    require_write: bool = False,
):
    """
    Get knowledge base and verify access.

    Args:
        kb_id: Knowledge base ID
        db: SQL database session
        current_user: Current user (None for guest)
        require_write: Whether write access is required

    Returns:
        KnowledgeBase instance

    Raises:
        HTTPException: If not found or access denied
    """
    kb = knowledge_base_service.get_by_id(db=db, kb_id=kb_id, user=current_user)

    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found or access denied",
        )

    if require_write and current_user:
        if not knowledge_base_service.can_modify(kb, current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to modify this knowledge base",
            )

    return kb


@router.post("/", response_model=Node, status_code=status.HTTP_201_CREATED)
def create_node(
    kb_id: str,
    node: NodeCreate,
    db: SQLSession = Depends(get_db),
    collection: Collection = Depends(get_chroma_collection),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new node in a knowledge base.

    Requires write access to the knowledge base.
    """
    # Verify KB access
    get_kb_with_access(kb_id, db, current_user, require_write=True)

    # Get session for this knowledge base's space
    for session in get_nebula_session_for_kb(kb_id):
        return graph_service.create_node(session, collection, node, kb_id)


@router.get("/", response_model=GraphData)
def get_all_nodes(
    kb_id: str,
    db: SQLSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all nodes and edges in a knowledge base.

    Returns the complete graph data for visualization.
    """
    # Verify KB access (read)
    get_kb_with_access(kb_id, db, current_user, require_write=False)

    # Get session for this knowledge base's space
    for session in get_nebula_session_for_kb(kb_id):
        return graph_service.get_graph_data(session)


@router.get("/{node_id}", response_model=Node)
def read_node(
    kb_id: str,
    node_id: str,
    db: SQLSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific node in a knowledge base.
    """
    # Verify KB access
    get_kb_with_access(kb_id, db, current_user, require_write=False)

    # Get session for this knowledge base's space
    for session in get_nebula_session_for_kb(kb_id):
        db_node = graph_service.get_node(session, node_id=node_id)
        if db_node is None:
            raise HTTPException(status_code=404, detail="Node not found")
        return db_node


@router.put("/{node_id}", response_model=Node)
def update_node(
    kb_id: str,
    node_id: str,
    node: NodeUpdate,
    db: SQLSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a node in a knowledge base.

    Requires write access to the knowledge base.
    """
    # Verify KB access
    get_kb_with_access(kb_id, db, current_user, require_write=True)

    # Get session for this knowledge base's space
    for session in get_nebula_session_for_kb(kb_id):
        db_node = graph_service.update_node(session, node_id=node_id, node=node)
        if db_node is None:
            raise HTTPException(status_code=404, detail="Node not found")
        return db_node


@router.delete("/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_node(
    kb_id: str,
    node_id: str,
    db: SQLSession = Depends(get_db),
    collection: Collection = Depends(get_chroma_collection),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a node from a knowledge base.

    Requires write access to the knowledge base.
    """
    # Verify KB access
    get_kb_with_access(kb_id, db, current_user, require_write=True)

    # Get session for this knowledge base's space
    for session in get_nebula_session_for_kb(kb_id):
        deleted = graph_service.delete_node(session, collection, node_id=node_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Node not found")


@router.post("/{node_id}/expand", response_model=List[Node])
def expand_node(
    kb_id: str,
    node_id: str,
    request: AIExpandRequest,
    db: SQLSession = Depends(get_db),
    collection: Collection = Depends(get_chroma_collection),
    current_user: User = Depends(get_current_user),
):
    """
    Expand a node using AI to generate related thoughts.

    Requires write access to the knowledge base.
    """
    # Verify KB access
    get_kb_with_access(kb_id, db, current_user, require_write=True)

    try:
        # Get session for this knowledge base's space
        for session in get_nebula_session_for_kb(kb_id):
            return ai_service.expand_node(
                session, collection, node_id, kb_id, request.instruction
            )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
