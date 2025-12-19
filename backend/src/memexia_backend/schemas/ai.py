from pydantic import BaseModel
from typing import Optional, List


class AIExpandRequest(BaseModel):
    """Request body for AI node expansion."""
    instruction: Optional[str] = None


class AIChatRequest(BaseModel):
    message: str
    context_node_ids: Optional[List[str]] = []
