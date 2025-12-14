from pydantic import BaseModel
from typing import Optional, List

class AIExpandRequest(BaseModel):
    node_id: str
    instruction: str

class AIChatRequest(BaseModel):
    message: str
    context_node_ids: Optional[List[str]] = []
