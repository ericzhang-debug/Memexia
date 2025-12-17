from fastapi import APIRouter, Depends
from neo4j import Session
from memexia_backend.database import get_neo4j_session
from memexia_backend.schemas import GraphData
from memexia_backend.services import graph_service

router = APIRouter(
    prefix="/api/v1/graph",
    tags=["graph"],
    responses={404: {"description": "Not found"}},
)

@router.get("/{knowledge_base_id}", response_model=GraphData)
def read_graph(knowledge_base_id: str, session: Session = Depends(get_neo4j_session)):
    return graph_service.get_graph_data(session, knowledge_base_id)
