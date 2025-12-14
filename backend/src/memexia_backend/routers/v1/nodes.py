from fastapi import APIRouter, Depends, HTTPException
from neo4j import Session
from chromadb.api.models.Collection import Collection
from typing import List
from memexia_backend.database import get_neo4j_session, get_chroma_collection
from memexia_backend.schemas import Node, NodeCreate, NodeUpdate, AIExpandRequest
from memexia_backend.services import graph_service, ai_service

router = APIRouter(
    prefix="/api/v1/nodes",
    tags=["nodes"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=Node)
def create_node(
    node: NodeCreate, 
    session: Session = Depends(get_neo4j_session),
    collection: Collection = Depends(get_chroma_collection)
):
    return graph_service.create_node(session, collection, node)

@router.get("/{node_id}", response_model=Node)
def read_node(node_id: str, session: Session = Depends(get_neo4j_session)):
    db_node = graph_service.get_node(session, node_id=node_id)
    if db_node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    return db_node

@router.put("/{node_id}", response_model=Node)
def update_node(
    node_id: str, 
    node: NodeUpdate, 
    session: Session = Depends(get_neo4j_session)
):
    db_node = graph_service.update_node(session, node_id=node_id, node=node)
    if db_node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    return db_node

@router.post("/{node_id}/expand", response_model=List[Node])
def expand_node(
    node_id: str, 
    request: AIExpandRequest, 
    session: Session = Depends(get_neo4j_session),
    collection: Collection = Depends(get_chroma_collection)
):
    try:
        return ai_service.expand_node(session, collection, node_id, request.instruction)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
