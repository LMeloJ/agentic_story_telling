"""
World state data models.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class Location(BaseModel):
    """A location in the story world."""
    
    location_id: str = Field(..., description="Unique location identifier")
    name: str = Field(..., description="Location name")
    description: str = Field(..., description="Location description")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Location-specific properties")
    npcs_present: List[str] = Field(default_factory=list, description="NPC IDs currently at this location")


class Event(BaseModel):
    """A story event."""
    
    event_id: str = Field(..., description="Unique event identifier")
    event_type: str = Field(..., description="Event type (conversation, action, discovery, etc.)")
    description: str = Field(..., description="Event description")
    timestamp: datetime = Field(default_factory=datetime.now, description="Event timestamp")
    participants: List[str] = Field(default_factory=list, description="NPC IDs involved in the event")
    consequences: Dict[str, Any] = Field(default_factory=dict, description="Event consequences and effects")
    importance: float = Field(default=0.5, ge=0.0, le=1.0, description="Event importance score")


class Relationship(BaseModel):
    """Relationship between two NPCs."""
    
    npc_id_1: str = Field(..., description="First NPC ID")
    npc_id_2: str = Field(..., description="Second NPC ID")
    relationship_score: float = Field(..., ge=-1.0, le=1.0, description="Relationship score (-1.0 to 1.0)")
    relationship_type: str = Field(default="neutral", description="Relationship type (friend, enemy, neutral, etc.)")
    history: List[str] = Field(default_factory=list, description="List of event IDs that affected this relationship")
    last_updated: datetime = Field(default_factory=datetime.now, description="Last relationship update timestamp")


class WorldState(BaseModel):
    """Complete world state for a story session."""
    
    story_id: str = Field(..., description="Unique story session identifier")
    current_location: Optional[str] = Field(default=None, description="Current location ID")
    locations: Dict[str, Location] = Field(default_factory=dict, description="All locations in the world")
    events: List[Event] = Field(default_factory=list, description="Story events that have occurred")
    relationships: Dict[str, Dict[str, Relationship]] = Field(
        default_factory=dict,
        description="NPC relationships (npc_id -> {other_npc_id -> Relationship})"
    )
    timeline: List[str] = Field(default_factory=list, description="Chronological list of event IDs")
    story_progression: Dict[str, Any] = Field(default_factory=dict, description="Story progression markers and flags")
    created_at: datetime = Field(default_factory=datetime.now, description="Story creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    version: int = Field(default=1, description="World state schema version")

