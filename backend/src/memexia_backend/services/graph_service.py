import uuid
from datetime import datetime
from typing import List, Optional
from neo4j import Session
from chromadb.api.models.Collection import Collection
from memexia_backend.schemas import NodeCreate, NodeUpdate, EdgeCreate, Node, Edge
from memexia_backend.services.embedding_service import embedding_service

def _map_node(record) -> Node:
    data = dict(record)
    # Neo4j stores datetime as specialized object or string, we stored as ISO string
    return Node(**data)

def _map_edge(record) -> Edge:
    # record is a Neo4j Relationship object
    # We need source and target IDs which are not directly on the relationship object in the result usually
    # So we usually query RETURN r, startNode(r).id, endNode(r).id
    # But let's assume the query returns a dict with these fields
    return Edge(**record)

def create_node(session: Session, collection: Collection, node: NodeCreate) -> Node:
    node_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    node_data = {
        "id": node_id,
        "content": node.content,
        "node_type": node.node_type,
        "created_at": now,
        "updated_at": now
    }
    
    # 1. Create in Neo4j
    query = (
        "CREATE (n:Node {id: $id, content: $content, node_type: $node_type, "
        "created_at: $created_at, updated_at: $updated_at}) "
        "RETURN n"
    )
    result = session.run(query, **node_data).single()
    created_node = _map_node(result["n"])
    
    # 2. Embed and store in ChromaDB
    embedding = embedding_service.generate_embedding(node.content)
    collection.add(
        ids=[node_id],
        embeddings=[embedding],
        metadatas=[{"content": node.content, "type": node.node_type}]
    )
    
    # 3. Find similar nodes and create edges
    # Check if there are enough nodes to query
    if collection.count() > 1:
        results = collection.query(
            query_embeddings=[embedding],
            n_results=4, # Top 3 similar + self
            include=["metadatas", "distances"]
        )
        
        similar_ids = results['ids'][0]
        distances = results['distances'][0]
        
        for i, target_id in enumerate(similar_ids):
            if target_id == node_id:
                continue
                
            # Chroma default is L2 (Squared Euclidean). Lower is closer.
            # Heuristic threshold
            if distances[i] < 1.5: 
                create_edge(session, EdgeCreate(
                    source_id=node_id,
                    target_id=target_id,
                    relation_type="SEMANTIC_RELATED",
                    weight=int((2.0 - distances[i]) * 10) # Simple weight formula
                ))

    return created_node

def get_node(session: Session, node_id: str) -> Optional[Node]:
    query = "MATCH (n:Node {id: $node_id}) RETURN n"
    result = session.run(query, node_id=node_id).single()
    if result:
        return _map_node(result["n"])
    return None

def update_node(session: Session, node_id: str, node: NodeUpdate) -> Optional[Node]:
    # Build SET clause dynamically
    fields = []
    params = {"node_id": node_id, "updated_at": datetime.now().isoformat()}
    
    if node.content is not None:
        fields.append("n.content = $content")
        params["content"] = node.content
    if node.node_type is not None:
        fields.append("n.node_type = $node_type")
        params["node_type"] = node.node_type
        
    fields.append("n.updated_at = $updated_at")
    
    set_clause = ", ".join(fields)
    query = f"MATCH (n:Node {{id: $node_id}}) SET {set_clause} RETURN n"
    
    result = session.run(query, **params).single()
    if result:
        return _map_node(result["n"])
    return None

def create_edge(session: Session, edge: EdgeCreate) -> Edge:
    edge_id = str(uuid.uuid4())
    query = (
        "MATCH (a:Node {id: $source_id}), (b:Node {id: $target_id}) "
        "MERGE (a)-[r:RELATED {id: $id, type: $relation_type}]->(b) "
        "SET r.weight = $weight "
        "RETURN r, a.id as source_id, b.id as target_id"
    )
    params = edge.dict()
    params["id"] = edge_id
    
    result = session.run(query, **params).single()
    if result:
        data = dict(result["r"])
        data["source_id"] = result["source_id"]
        data["target_id"] = result["target_id"]
        data["relation_type"] = result["r"]["type"] # Neo4j stores type separately usually, but we stored it as prop too? No, [r:RELATED] is the type.
        # Actually, let's simplify. We used dynamic type in previous code but Cypher doesn't support dynamic types in MERGE easily without APOC.
        # For simplicity, we'll use a generic 'RELATED' type and store the specific type as a property 'relation_type'
        # OR we use APOC. But let's stick to standard Cypher.
        # Let's just use one relationship type 'LINKS_TO' and store 'relation_type' as property.
        return Edge(**data)
    return None

def get_graph_data(session: Session):
    # Get all nodes
    nodes_query = "MATCH (n:Node) RETURN n"
    nodes_result = session.run(nodes_query)
    nodes = [_map_node(record["n"]) for record in nodes_result]
    
    # Get all edges
    edges_query = "MATCH (a)-[r]->(b) RETURN r, a.id as source_id, b.id as target_id"
    edges_result = session.run(edges_query)
    edges = []
    for record in edges_result:
        data = dict(record["r"])
        data["source_id"] = record["source_id"]
        data["target_id"] = record["target_id"]
        # data["relation_type"] = ... # If we stored it
        edges.append(Edge(**data))
        
    return {"nodes": nodes, "edges": edges}

