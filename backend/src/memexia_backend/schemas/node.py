from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class NodeBase(BaseModel):
    content: str
    node_type: str = "concept"

class NodeCreate(NodeBase):
    pass

class NodeUpdate(BaseModel):
    content: Optional[str] = None
    node_type: Optional[str] = None

class Node(NodeBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
