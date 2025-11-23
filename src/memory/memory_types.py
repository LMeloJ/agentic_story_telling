"""
Memory types for the memory system.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class Memory(BaseModel):
    """A retrieved memory from the memory system."""
    
    chunk_id: str = Field(..., description="Memory chunk identifier")
    content: str = Field(..., description="Memory content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Memory metadata")
    score: float = Field(default=0.0, description="Relevance score")
    timestamp: Optional[datetime] = Field(default=None, description="Memory timestamp")

