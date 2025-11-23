"""
Story configuration data model.
"""

from typing import List, Dict, Any
from pydantic import BaseModel, Field

from src.models.npc_profile import NPCProfile
from src.models.world_state import WorldState


class StoryConfig(BaseModel):
    """Configuration for starting a new story session."""
    
    story_id: str = Field(..., description="Unique story session identifier")
    npc_profiles: List[NPCProfile] = Field(..., description="List of NPC profiles for this story")
    initial_world_state: Dict[str, Any] = Field(default_factory=dict, description="Initial world state configuration")
    story_settings: Dict[str, Any] = Field(default_factory=dict, description="Story-specific settings")

