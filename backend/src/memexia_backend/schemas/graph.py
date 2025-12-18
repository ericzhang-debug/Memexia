from pydantic import BaseModel
from typing import List

from .node import Node
from .edge import Edge

class GraphData(BaseModel):
    nodes: List[Node]
    edges: List[Edge]
