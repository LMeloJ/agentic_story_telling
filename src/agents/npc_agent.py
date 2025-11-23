"""
NPC Agent interface and base implementation.
"""

from abc import ABC, abstractmethod
from typing import Optional

from src.models.npc_profile import NPCProfile
from src.models.conversation import ConversationContext, Message, Conversation


class NPCAgent(ABC):
    """
    Abstract base class for NPC Agent API.
    
    Defines the interface for NPC agents that generate contextual responses
    using Gemini API and maintain conversation memory.
    """
    
    @abstractmethod
    def initialize(self, npc_id: str, profile: NPCProfile) -> None:
        """
        Initialize an NPC agent with its profile.
        
        Args:
            npc_id: Unique identifier for the NPC
            profile: NPC profile containing personality, backstory, goals, etc.
        """
        pass
    
    @abstractmethod
    def generate_response(self, context: ConversationContext) -> str:
        """
        Generate a dialog response for the NPC.
        
        Args:
            context: Current conversation context including history, memories, world state
        
        Returns:
            Generated dialog text
        """
        pass
    
    @abstractmethod
    def update_memory(self, conversation: Conversation) -> None:
        """
        Store a new conversation in the NPC's memory.
        
        Args:
            conversation: Conversation object with messages and metadata
        """
        pass
    
    @abstractmethod
    def get_npc_id(self) -> str:
        """Get the NPC ID for this agent."""
        pass
    
    @abstractmethod
    def get_profile(self) -> NPCProfile:
        """Get the NPC profile for this agent."""
        pass

