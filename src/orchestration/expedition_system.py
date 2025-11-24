"""
Expedition event system for story progression.

Handles expeditions where NPCs gather materials, and events that occur
during expeditions that NPCs may or may not share with others.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

from src.services.gemini_service import GeminiService
from src.services.logging_service import get_logger


class ExpeditionType(str, Enum):
    """Types of expeditions NPCs can undertake."""
    GATHER_MATERIALS = "gather_materials"  # For fixing communication device
    GATHER_FOOD = "gather_food"
    GATHER_WATER = "gather_water"
    GATHER_MEDICINAL_PLANTS = "gather_medicinal_plants"
    SCOUT_AREA = "scout_area"
    EXPLORE = "explore"


class ExpeditionEvent(BaseModel):
    """An event that occurs during an expedition."""
    
    event_id: str = Field(..., description="Unique event identifier")
    expedition_id: str = Field(..., description="Expedition this event belongs to")
    event_type: str = Field(..., description="Type of event (discovery, danger, success, etc.)")
    description: str = Field(..., description="What happened during the expedition")
    npc_id: str = Field(..., description="NPC who experienced this event")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the event occurred")
    materials_found: Dict[str, int] = Field(default_factory=dict, description="Materials found (type -> quantity)")
    is_shared: bool = Field(default=False, description="Whether NPC has shared this information")
    importance: float = Field(default=0.5, ge=0.0, le=1.0, description="Event importance score")
    consequences: Dict[str, Any] = Field(default_factory=dict, description="Consequences of this event")


class Expedition(BaseModel):
    """An expedition undertaken by NPCs."""
    
    expedition_id: str = Field(..., description="Unique expedition identifier")
    expedition_type: ExpeditionType = Field(..., description="Type of expedition")
    npc_ids: List[str] = Field(..., description="NPCs participating in this expedition")
    goal: str = Field(..., description="Goal of the expedition")
    started_at: datetime = Field(default_factory=datetime.now, description="When expedition started")
    completed_at: Optional[datetime] = Field(default=None, description="When expedition completed")
    events: List[ExpeditionEvent] = Field(default_factory=list, description="Events that occurred during expedition")
    success: bool = Field(default=False, description="Whether expedition was successful")
    materials_gathered: Dict[str, int] = Field(default_factory=dict, description="Total materials gathered")


class ExpeditionAgent:
    """
    Agent that decides what happens during expeditions.
    
    Uses Gemini API to generate realistic expedition events based on:
    - Expedition type and goal
    - NPCs participating
    - Current world state
    - Story context
    """
    
    def __init__(self, gemini_service: GeminiService):
        """
        Initialize expedition agent.
        
        Args:
            gemini_service: Gemini service for generating expedition events
        """
        self.gemini_service = gemini_service
        self.logger = get_logger("expedition_agent")
    
    def generate_expedition_events(
        self,
        expedition: Expedition,
        npc_profiles: Dict[str, Any],
        world_state: Dict[str, Any],
    ) -> List[ExpeditionEvent]:
        """
        Generate events that occur during an expedition.
        
        Args:
            expedition: The expedition to generate events for
            npc_profiles: Dictionary of NPC profiles (npc_id -> profile dict)
            world_state: Current world state
            
        Returns:
            List of events that occurred during the expedition
        """
        self.logger.info(f"Generating events for expedition {expedition.expedition_id}")
        
        # Build prompt for Gemini to generate expedition events
        prompt = self._build_expedition_prompt(expedition, npc_profiles, world_state)
        
        try:
            # Generate events using Gemini
            response = self.gemini_service.generate_response(
                prompt=prompt,
                temperature=0.8,  # Higher temperature for more creative events
            )
            
            # Parse response into events
            events = self._parse_events_from_response(response, expedition)
            
            self.logger.info(f"Generated {len(events)} events for expedition {expedition.expedition_id}")
            return events
            
        except Exception as e:
            self.logger.error(f"Error generating expedition events: {e}")
            # Return a default event on error
            return [self._create_default_event(expedition)]
    
    def _build_expedition_prompt(
        self,
        expedition: Expedition,
        npc_profiles: Dict[str, Any],
        world_state: Dict[str, Any],
    ) -> str:
        """Build prompt for Gemini to generate expedition events."""
        npc_descriptions = []
        for npc_id in expedition.npc_ids:
            profile = npc_profiles.get(npc_id, {})
            npc_descriptions.append(
                f"- {profile.get('name', npc_id)}: {profile.get('backstory', 'Unknown character')}"
            )
        
        prompt = f"""You are a story event generator for an immersive storytelling game.

Context:
- Three NPCs (a captain, a doctor, and an engineer) crashed their airship on a snowy island.
- The captain has severely injured legs and cannot go on expeditions.
- They are trying to survive and fix their communication device.

Current Expedition:
- Type: {expedition.expedition_type.value}
- Goal: {expedition.goal}
- Participants: {', '.join(expedition.npc_ids)}
- NPC Details:
{chr(10).join(npc_descriptions)}

World State:
- Location: {world_state.get('current_location', 'Unknown')}
- Day: {world_state.get('day', 1)}
- Weather: {world_state.get('weather', 'snowy and cold')}

Generate 2-4 realistic events that occur during this expedition. Events should:
1. Be appropriate for the expedition type and goal
2. Reflect the harsh, snowy island environment
3. Include discoveries, challenges, or dangers
4. Be specific and immersive
5. Include QUANTITATIVE results for materials found

IMPORTANT: For materials_found, use specific quantities based on expedition type:
- GATHER_MATERIALS: Use units like {{"metal_scraps": 5, "wires": 3, "electronic_components": 2}}
- GATHER_FOOD: Use units like {{"food_units": 8}} (1 unit = 1 day of food for 1 person)
- GATHER_WATER: Use liters like {{"water_liters": 12}} (liters of clean water)
- GATHER_MEDICINAL_PLANTS: Use doses like {{"medicine_doses": 6}} (1 dose treats 1 person for 1 day)

Format your response as a JSON array of events, where each event has:
- event_type: string (e.g., "discovery", "danger", "success", "failure", "encounter")
- description: string (detailed description of what happened, including specific quantities found)
- materials_found: object with material types and QUANTITATIVE amounts (e.g., {{"water_liters": 12, "food_units": 5}})
- importance: float between 0.0 and 1.0 (how important this event is to the story)

Example format for GATHER_WATER:
[
  {{
    "event_type": "discovery",
    "description": "Found a small stream partially frozen. Managed to collect 8 liters of clean water by melting ice.",
    "materials_found": {{"water_liters": 8}},
    "importance": 0.7
  }},
  {{
    "event_type": "success",
    "description": "Discovered a natural spring. Collected an additional 4 liters of fresh water.",
    "materials_found": {{"water_liters": 4}},
    "importance": 0.6
  }}
]

Example format for GATHER_FOOD:
[
  {{
    "event_type": "discovery",
    "description": "Found a patch of edible berries. Collected enough for 6 days of food.",
    "materials_found": {{"food_units": 6}},
    "importance": 0.7
  }}
]

Generate events now with QUANTITATIVE results:"""
        
        return prompt
    
    def _parse_events_from_response(self, response: str, expedition: Expedition) -> List[ExpeditionEvent]:
        """Parse Gemini response into ExpeditionEvent objects."""
        import json
        import re
        
        events = []
        
        try:
            # Try to extract JSON from response
            # Look for JSON array in the response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                events_data = json.loads(json_match.group())
            else:
                # Try parsing the whole response as JSON
                events_data = json.loads(response)
            
            for i, event_data in enumerate(events_data):
                event = ExpeditionEvent(
                    event_id=f"{expedition.expedition_id}_event_{i+1}",
                    expedition_id=expedition.expedition_id,
                    event_type=event_data.get("event_type", "unknown"),
                    description=event_data.get("description", "Something happened."),
                    npc_id=expedition.npc_ids[0] if expedition.npc_ids else "unknown",  # Primary NPC
                    materials_found=event_data.get("materials_found", {}),
                    importance=event_data.get("importance", 0.5),
                )
                events.append(event)
                
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            self.logger.warning(f"Failed to parse events from response: {e}. Creating default event.")
            events = [self._create_default_event(expedition)]
        
        return events
    
    def _create_default_event(self, expedition: Expedition) -> ExpeditionEvent:
        """Create a default event when parsing fails."""
        return ExpeditionEvent(
            event_id=f"{expedition.expedition_id}_event_default",
            expedition_id=expedition.expedition_id,
            event_type="exploration",
            description=f"The expedition to {expedition.goal} was completed with some success.",
            npc_id=expedition.npc_ids[0] if expedition.npc_ids else "unknown",
            materials_found={},
            importance=0.5,
        )

