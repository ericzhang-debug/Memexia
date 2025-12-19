"""
Graph API routes for retrieving full graph data.

Each knowledge base has its own database/space for data isolation.
"""

from fastapi import APIRouter
from memexia_backend.schemas import GraphData
from memexia_backend.services import graph_service

router = APIRouter(
    prefix="/api/v1/graph",
    tags=["graph"],
    responses={404: {"description": "Not found"}},
)


@router.get("/{knowledge_base_id}", response_model=GraphData)
def read_graph(knowledge_base_id: str):
    """
    Get all graph data for a knowledge base.

    Returns nodes and edges for visualization.
    """
    return graph_service.get_graph_data(knowledge_base_id)
