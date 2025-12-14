from pydantic import BaseModel
from typing import Optional

class EdgeBase(BaseModel):
    source_id: str
    target_id: str
    relation_type: str = "related"
    weight: int = 1

class EdgeCreate(EdgeBase):
    pass

class Edge(EdgeBase):
    id: str

    class Config:
        from_attributes = True
