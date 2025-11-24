"""
Concrete implementation of Story Orchestrator.

Manages story progression, multi-NPC conversations, expeditions,
and world state updates for the crashed airship scenario.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from src.orchestration.story_orchestrator import StoryOrchestrator
from src.orchestration.story_config import StoryConfig
from src.orchestration.expedition_system import (
    Expedition,
    ExpeditionType,
    ExpeditionAgent,
    ExpeditionEvent,
)
from src.orchestration.multi_party_conversation import (
    MultiPartyConversation,
    TurnTakingStrategy,
    ConversationTurn,
)
from src.orchestration.world_state_utils import serialize_world_state
from src.models.world_state import WorldState, Location, Event, Relationship
from src.models.conversation import ConversationContext, Message, Conversation
from src.models.npc_profile import NPCProfile
from src.agents.npc_agent import NPCAgent
from src.memory.memory_system import MemorySystem
from src.services.gemini_service import GeminiService
from src.services.logging_service import get_logger


class ConcreteStoryOrchestrator(StoryOrchestrator):
    """
    Concrete implementation of Story Orchestrator.
    
    Manages:
    - Story initialization and state
    - Multi-NPC conversations (e.g., around bonfire)
    - Expedition planning and execution
    - World state updates
    - Relationship tracking
    """
    
    def __init__(
        self,
        npc_agents: Dict[str, NPCAgent],
        memory_system: MemorySystem,
        gemini_service: GeminiService,
        turn_strategy: TurnTakingStrategy = TurnTakingStrategy.NATURAL,
    ):
        """
        Initialize story orchestrator.
        
        Args:
            npc_agents: Dictionary of initialized NPC agents (npc_id -> NPCAgent)
            memory_system: Memory system for storing conversations
            gemini_service: Gemini service for expedition events and decisions
            turn_strategy: Strategy for turn-taking in conversations
        """
        self.npc_agents = npc_agents
        self.memory_system = memory_system
        self.gemini_service = gemini_service
        self.turn_strategy = turn_strategy
        self.logger = get_logger("story_orchestrator")
        
        # Story state storage (in-memory for now, can be upgraded to persistent)
        self.story_states: Dict[str, WorldState] = {}
        
        # Expedition agent
        self.expedition_agent = ExpeditionAgent(gemini_service)
        
        # Active conversations per story
        self.active_conversations: Dict[str, MultiPartyConversation] = {}
        
        # Expedition tracking
        self.active_expeditions: Dict[str, Expedition] = {}
        self.completed_expeditions: Dict[str, List[Expedition]] = {}
    
    def start_story(self, story_config: StoryConfig) -> WorldState:
        """
        Initialize a new story session.
        
        Args:
            story_config: Story configuration including NPCs and initial world state
            
        Returns:
            Initial world state
        """
        self.logger.info(f"Starting story: {story_config.story_id}")
        
        # Initialize NPC agents if not already initialized
        for profile in story_config.npc_profiles:
            if profile.npc_id not in self.npc_agents:
                raise ValueError(f"NPC agent for {profile.npc_id} not provided")
            self.npc_agents[profile.npc_id].initialize(profile.npc_id, profile)
        
        # Create initial world state
        world_state = self._create_initial_world_state(story_config)
        
        # Store world state
        self.story_states[story_config.story_id] = world_state
        
        # Initialize multi-party conversation
        conversation = MultiPartyConversation(
            npc_agents=self.npc_agents,
            turn_strategy=self.turn_strategy,
            gemini_service=self.gemini_service,
        )
        self.active_conversations[story_config.story_id] = conversation
        
        # Initialize expedition tracking
        self.completed_expeditions[story_config.story_id] = []
        
        self.logger.info(f"Story {story_config.story_id} initialized with {len(story_config.npc_profiles)} NPCs")
        return world_state
    
    def _create_initial_world_state(self, story_config: StoryConfig) -> WorldState:
        """Create initial world state from story configuration."""
        # Create bonfire location
        bonfire_location = Location(
            location_id="bonfire_campsite",
            name="Bonfire Campsite",
            description="A small campsite around a bonfire where the crew gathers to plan and share experiences.",
            properties={
                "temperature": "warm",
                "safety": "relatively_safe",
                "visibility": "good",
            },
            npcs_present=[profile.npc_id for profile in story_config.npc_profiles],
        )
        
        # Create crashed airship location
        airship_location = Location(
            location_id="crashed_airship",
            name="Crashed Airship",
            description="The remains of the expedition's airship, crashed on the snowy island.",
            properties={
                "condition": "severely_damaged",
                "salvageable_parts": True,
            },
            npcs_present=[],
        )
        
        # Create initial event (crash)
        crash_event = Event(
            event_id="initial_crash",
            event_type="catastrophe",
            description="The airship crashed on a snowy island. The captain severely injured his legs.",
            participants=[profile.npc_id for profile in story_config.npc_profiles],
            importance=1.0,
            consequences={
                "captain_injured": True,
                "communication_device_damaged": True,
                "stranded": True,
            },
        )
        
        # Initialize relationships
        relationships = {}
        for profile in story_config.npc_profiles:
            relationships[profile.npc_id] = {}
            for other_profile in story_config.npc_profiles:
                if profile.npc_id != other_profile.npc_id:
                    rel_score = profile.relationships.get(other_profile.npc_id, 0.0)
                    relationships[profile.npc_id][other_profile.npc_id] = Relationship(
                        npc_id_1=profile.npc_id,
                        npc_id_2=other_profile.npc_id,
                        relationship_score=rel_score,
                        relationship_type="crew_member",
                    )
        
        # Create world state
        world_state = WorldState(
            story_id=story_config.story_id,
            current_location="bonfire_campsite",
            locations={
                "bonfire_campsite": bonfire_location,
                "crashed_airship": airship_location,
            },
            events=[crash_event],
            relationships=relationships,
            timeline=["initial_crash"],
            story_progression={
                "day": 1,
                "weather": "snowy_and_cold",
                "materials_collected": {},
                "communication_device_status": "broken",
                "captain_condition": "severely_injured_legs",
                "water_liters": 0,
                "food_units": 0,
                "medicine_doses": 0,
                "water_supplies": "low",
                "food_supplies": "low",
                "medicine_supplies": "none",
            },
        )
        
        # Merge with any custom initial world state from config
        if story_config.initial_world_state:
            world_state.story_progression.update(story_config.initial_world_state)
        
        return world_state
    
    def progress_story(
        self,
        player_input: Optional[str],
        story_state: WorldState,
    ) -> WorldState:
        """
        Process player input (or auto-progress) and advance the story.
        
        Args:
            player_input: Optional player input/message
            story_state: Current story state
            
        Returns:
            Updated story state
        """
        story_id = story_state.story_id
        self.logger.info(f"Progressing story {story_id}")
        
        # Get active conversation
        conversation = self.active_conversations.get(story_id)
        if not conversation:
            # Initialize conversation if it doesn't exist
            conversation = MultiPartyConversation(
                npc_agents=self.npc_agents,
                turn_strategy=self.turn_strategy,
                gemini_service=self.gemini_service,
            )
            self.active_conversations[story_id] = conversation
        
        # Get available NPCs (all NPCs at current location)
        current_location = story_state.locations.get(story_state.current_location)
        available_npcs = current_location.npcs_present if current_location else list(self.npc_agents.keys())
        
        # Generate conversation turns
        num_turns = 3  # Generate a few turns of conversation
        for _ in range(num_turns):
            # Determine next speaker
            world_state_dict = story_state.model_dump() if hasattr(story_state, 'model_dump') else story_state.dict()
            world_state_dict = serialize_world_state(world_state_dict)
            next_speaker = conversation.get_next_speaker(available_npcs, world_state_dict)
            if not next_speaker:
                break
            
            # Get expedition events for this NPC (if any)
            expedition_events = self._get_npc_expedition_events(next_speaker, story_id)
            
            # Build conversation context
            world_state_dict = story_state.model_dump() if hasattr(story_state, 'model_dump') else story_state.dict()
            world_state_dict = serialize_world_state(world_state_dict)
            context = ConversationContext(
                npc_id=next_speaker,
                conversation_history=conversation.conversation_history[-10:],  # Last 10 messages
                retrieved_memories=[],
                world_state=world_state_dict,
                player_input=player_input,
                metadata={
                    "location": story_state.current_location,
                    "day": story_state.story_progression.get("day", 1),
                },
            )
            
            # Add turn to conversation
            turn = conversation.add_turn(
                npc_id=next_speaker,
                context=context,
                world_state=world_state_dict,
                expedition_events=expedition_events,
            )
            
            # Update world state based on conversation
            story_state = self._update_world_state_from_turn(story_state, turn)
            
            # Store conversation in memory
            self._store_conversation_turn(story_id, turn)
        
        # Update story state timestamp
        story_state.updated_at = datetime.now()
        
        # Save updated state
        self.story_states[story_id] = story_state
        
        return story_state
    
    def _get_npc_expedition_events(
        self,
        npc_id: str,
        story_id: str,
    ) -> Optional[List[Dict[str, Any]]]:
        """Get expedition events for an NPC that haven't been shared yet."""
        # Check completed expeditions for this story
        completed = self.completed_expeditions.get(story_id, [])
        
        events = []
        for expedition in completed:
            if npc_id in expedition.npc_ids:
                for event in expedition.events:
                    if not event.is_shared:
                        events.append({
                            "event_id": event.event_id,
                            "event_type": event.event_type,
                            "description": event.description,
                            "materials_found": event.materials_found,
                            "importance": event.importance,
                        })
        
        return events if events else None
    
    def _update_world_state_from_turn(
        self,
        world_state: WorldState,
        turn: ConversationTurn,
    ) -> WorldState:
        """Update world state based on a conversation turn."""
        # Create event for this conversation turn
        event = Event(
            event_id=f"conversation_turn_{turn.turn_id}",
            event_type="conversation",
            description=f"{turn.npc_id} said: {turn.message[:100]}...",
            participants=[turn.npc_id],
            importance=0.3,
        )
        
        world_state.events.append(event)
        world_state.timeline.append(event.event_id)
        
        # Update materials if shared information mentions materials
        shared_info = turn.shared_information
        if shared_info and isinstance(shared_info.get("events_to_share"), list):
            for event_info in shared_info["events_to_share"]:
                if isinstance(event_info, dict) and "materials_found" in event_info:
                    materials = event_info["materials_found"]
                    for material, quantity in materials.items():
                        current = world_state.story_progression.get("materials_collected", {})
                        current[material] = current.get(material, 0) + quantity
                        world_state.story_progression["materials_collected"] = current
        
        return world_state
    
    def _store_conversation_turn(self, story_id: str, turn: ConversationTurn) -> None:
        """Store a conversation turn in memory."""
        try:
            # Create conversation object
            conversation = Conversation(
                conversation_id=f"{story_id}_{turn.turn_id}",
                npc_id=turn.npc_id,
                messages=[
                    Message(
                        role="npc",
                        content=turn.message,
                        npc_id=turn.npc_id,
                        metadata={"turn_number": turn.turn_number},
                    )
                ],
                importance_score=0.5,
            )
            
            # Store in NPC's memory
            agent = self.npc_agents.get(turn.npc_id)
            if agent:
                agent.update_memory(conversation)
                
        except Exception as e:
            self.logger.warning(f"Error storing conversation turn: {e}")
    
    def create_expedition(
        self,
        story_id: str,
        expedition_type: ExpeditionType,
        npc_ids: List[str],
        goal: str,
    ) -> Expedition:
        """
        Create and execute an expedition.
        
        Args:
            story_id: Story session ID
            expedition_type: Type of expedition
            npc_ids: NPCs participating in the expedition
            goal: Goal of the expedition
            
        Returns:
            Completed expedition with events
        """
        self.logger.info(f"Creating expedition: {expedition_type.value} with NPCs: {npc_ids}")
        
        # Create expedition
        expedition = Expedition(
            expedition_id=f"expedition_{uuid.uuid4().hex[:8]}",
            expedition_type=expedition_type,
            npc_ids=npc_ids,
            goal=goal,
        )
        
        # Get world state
        world_state = self.story_states.get(story_id)
        if not world_state:
            raise ValueError(f"Story {story_id} not found")
        
        # Get NPC profiles
        npc_profiles = {}
        for npc_id in npc_ids:
            agent = self.npc_agents.get(npc_id)
            if agent:
                profile = agent.get_profile()
                npc_profiles[npc_id] = {
                    "name": profile.name,
                    "backstory": profile.backstory,
                    "personality": (
                        profile.personality.model_dump() 
                        if hasattr(profile.personality, 'model_dump') 
                        else profile.personality.dict()
                    ) if profile.personality else {},
                }
        
        # Generate expedition events
        world_state_dict = world_state.model_dump() if hasattr(world_state, 'model_dump') else world_state.dict()
        world_state_dict = serialize_world_state(world_state_dict)
        events = self.expedition_agent.generate_expedition_events(
            expedition=expedition,
            npc_profiles=npc_profiles,
            world_state=world_state_dict,
        )
        
        expedition.events = events
        expedition.completed_at = datetime.now()
        
        # Calculate materials gathered
        for event in events:
            for material, quantity in event.materials_found.items():
                expedition.materials_gathered[material] = (
                    expedition.materials_gathered.get(material, 0) + quantity
                )
        
        expedition.success = len(expedition.materials_gathered) > 0 or any(
            e.event_type in ["success", "discovery"] for e in events
        )
        
        # Store expedition
        if story_id not in self.completed_expeditions:
            self.completed_expeditions[story_id] = []
        self.completed_expeditions[story_id].append(expedition)
        
        # Update world state with expedition results
        world_state = self._update_world_state_from_expedition(world_state, expedition)
        self.story_states[story_id] = world_state
        
        self.logger.info(f"Expedition {expedition.expedition_id} completed. Success: {expedition.success}")
        return expedition
    
    def _update_world_state_from_expedition(
        self,
        world_state: WorldState,
        expedition: Expedition,
    ) -> WorldState:
        """Update world state based on expedition results."""
        # Create expedition event
        event = Event(
            event_id=f"expedition_{expedition.expedition_id}",
            event_type="expedition",
            description=f"Expedition to {expedition.goal} completed. Success: {expedition.success}",
            participants=expedition.npc_ids,
            importance=0.7,
            consequences={
                "materials_gathered": expedition.materials_gathered,
                "success": expedition.success,
            },
        )
        
        world_state.events.append(event)
        world_state.timeline.append(event.event_id)
        
        # Update materials in story progression
        for material, quantity in expedition.materials_gathered.items():
            current = world_state.story_progression.get("materials_collected", {})
            current[material] = current.get(material, 0) + quantity
            world_state.story_progression["materials_collected"] = current
        
        # Update resource levels based on expedition type
        self._update_resource_levels(world_state, expedition)
        
        return world_state
    
    def _update_resource_levels(
        self,
        world_state: WorldState,
        expedition: Expedition,
    ) -> None:
        """Update resource supply levels based on expedition results."""
        # Track resource levels
        if "water_supplies" not in world_state.story_progression:
            world_state.story_progression["water_supplies"] = "low"
        if "food_supplies" not in world_state.story_progression:
            world_state.story_progression["food_supplies"] = "low"
        if "medicine_supplies" not in world_state.story_progression:
            world_state.story_progression["medicine_supplies"] = "none"
        
        # Update based on materials gathered
        water_liters = expedition.materials_gathered.get("water_liters", 0)
        food_units = expedition.materials_gathered.get("food_units", 0)
        medicine_doses = expedition.materials_gathered.get("medicine_doses", 0)
        
        # Update water supplies
        if water_liters > 0:
            current_water = world_state.story_progression.get("water_liters", 0)
            new_water = current_water + water_liters
            world_state.story_progression["water_liters"] = new_water
            
            # Update supply level
            if new_water >= 20:
                world_state.story_progression["water_supplies"] = "high"
            elif new_water >= 10:
                world_state.story_progression["water_supplies"] = "medium"
            else:
                world_state.story_progression["water_supplies"] = "low"
        
        # Update food supplies
        if food_units > 0:
            current_food = world_state.story_progression.get("food_units", 0)
            new_food = current_food + food_units
            world_state.story_progression["food_units"] = new_food
            
            # Update supply level
            if new_food >= 15:
                world_state.story_progression["food_supplies"] = "high"
            elif new_food >= 8:
                world_state.story_progression["food_supplies"] = "medium"
            else:
                world_state.story_progression["food_supplies"] = "low"
        
        # Update medicine supplies
        if medicine_doses > 0:
            current_medicine = world_state.story_progression.get("medicine_doses", 0)
            new_medicine = current_medicine + medicine_doses
            world_state.story_progression["medicine_doses"] = new_medicine
            
            # Update supply level
            if new_medicine >= 10:
                world_state.story_progression["medicine_supplies"] = "high"
            elif new_medicine >= 5:
                world_state.story_progression["medicine_supplies"] = "medium"
            else:
                world_state.story_progression["medicine_supplies"] = "low"
    
    def get_state(self, story_id: str) -> Optional[WorldState]:
        """
        Retrieve current story state.
        
        Args:
            story_id: Story session identifier
            
        Returns:
            Current world state, or None if not found
        """
        return self.story_states.get(story_id)
    
    def get_conversation_history(self, story_id: str) -> List[ConversationTurn]:
        """Get conversation history for a story."""
        conversation = self.active_conversations.get(story_id)
        if conversation:
            return conversation.turns
        return []
    
    def get_expeditions(self, story_id: str) -> List[Expedition]:
        """Get all expeditions for a story."""
        return self.completed_expeditions.get(story_id, [])

