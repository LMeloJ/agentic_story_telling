"""
Memory chunk data models.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class MemoryMetadata(BaseModel):
    """Metadata for a memory chunk."""
    
    npc_id: Optional[str] = Field(default=None, description="NPC ID associated with this memory")
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID this memory belongs to")
    timestamp: datetime = Field(default_factory=datetime.now, description="Memory timestamp")
    importance_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Importance score for retrieval")
    memory_type: str = Field(default="conversation", description="Memory type (conversation, event, relationship, etc.)")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    additional_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class MemoryChunk(BaseModel):
    """A memory chunk stored in ChromaDB."""
    
    chunk_id: str = Field(..., description="Unique memory chunk identifier")
    content: str = Field(..., description="Memory content/text")
    embedding: Optional[List[float]] = Field(default=None, description="Embedding vector (if available)")
    metadata: MemoryMetadata = Field(..., description="Memory metadata")
    collection: str = Field(default="npc_memories", description="ChromaDB collection name")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    last_accessed: Optional[datetime] = Field(default=None, description="Last access timestamp")

