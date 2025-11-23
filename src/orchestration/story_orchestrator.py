"""
Story Orchestrator interface and base implementation.
"""

from abc import ABC, abstractmethod
from typing import Optional

from src.models.world_state import WorldState
from src.orchestration.story_config import StoryConfig


class StoryOrchestrator(ABC):
    """
    Abstract base class for Story Orchestrator API.
    
    Manages narrative flow, coordinates multi-NPC interactions,
    and handles world state updates.
    """
    
    @abstractmethod
    def start_story(self, story_config: StoryConfig) -> WorldState:
        """
        Initialize a new story session.
        
        Args:
            story_config: Story configuration including NPCs, initial world state
        
        Returns:
            Initial story state
        """
        pass
    
    @abstractmethod
    def progress_story(self, player_input: str, story_state: WorldState) -> WorldState:
        """
        Process player input and advance the story.
        
        Args:
            player_input: Player's message or action
            story_state: Current story state
        
        Returns:
            Updated story state
        """
        pass
    
    @abstractmethod
    def get_state(self, story_id: str) -> Optional[WorldState]:
        """
        Retrieve current story state.
        
        Args:
            story_id: Story session identifier
        
        Returns:
            Current story state, or None if not found
        """
        pass

