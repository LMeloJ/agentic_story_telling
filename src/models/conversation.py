"""
Conversation and message data models.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class Message(BaseModel):
    """A single message in a conversation."""
    
    role: str = Field(..., description="Message role: 'user', 'npc', or 'system'")
    content: str = Field(..., description="Message content/text")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")
    npc_id: Optional[str] = Field(default=None, description="NPC ID if message is from an NPC")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class Conversation(BaseModel):
    """A conversation between user and NPC(s)."""
    
    conversation_id: str = Field(..., description="Unique conversation identifier")
    npc_id: Optional[str] = Field(default=None, description="Primary NPC ID (if single NPC conversation)")
    messages: List[Message] = Field(default_factory=list, description="List of messages in the conversation")
    context: Dict[str, Any] = Field(default_factory=dict, description="Conversation context metadata")
    created_at: datetime = Field(default_factory=datetime.now, description="Conversation creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    importance_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Importance score for memory retention")


class ConversationContext(BaseModel):
    """Context for generating NPC responses."""
    
    npc_id: str = Field(..., description="NPC generating the response")
    conversation_history: List[Message] = Field(default_factory=list, description="Recent conversation history")
    retrieved_memories: List[str] = Field(default_factory=list, description="Retrieved memory chunk IDs")
    world_state: Dict[str, Any] = Field(default_factory=dict, description="Current world state")
    player_input: Optional[str] = Field(default=None, description="Current player input/message")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context metadata")

