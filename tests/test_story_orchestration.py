"""
Tests for story orchestration system (Phase 4).

Tests multi-NPC conversations, expeditions, and world state management.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch

from src.orchestration.story_config import StoryConfig
from src.orchestration.concrete_orchestrator import ConcreteStoryOrchestrator
from src.orchestration.expedition_system import (
    Expedition,
    ExpeditionType,
    ExpeditionEvent,
    ExpeditionAgent,
)
from src.orchestration.multi_party_conversation import (
    MultiPartyConversation,
    TurnTakingStrategy,
)
from src.models.world_state import WorldState, Location, Event
from src.models.npc_profile import NPCProfile, PersonalityTraits, SpeechPatterns, VoiceConfig
from src.agents.npc_agent import NPCAgent
from src.memory.memory_system import MemorySystem
from src.services.gemini_service import GeminiService


@pytest.fixture
def mock_memory_system():
    """Create a mock memory system."""
    memory = Mock(spec=MemorySystem)
    memory.store = Mock(return_value="memory_id_123")
    memory.retrieve = Mock(return_value=[])
    memory.update = Mock(return_value=True)
    memory.search = Mock(return_value=[])
    memory.delete = Mock(return_value=True)
    memory.get_collection_info = Mock(return_value={"count": 0})
    return memory


@pytest.fixture
def mock_gemini_service():
    """Create a mock Gemini service."""
    service = Mock(spec=GeminiService)
    service.generate_content = Mock(return_value="Mock response")
    return service


@pytest.fixture
def sample_npc_profiles():
    """Create sample NPC profiles for testing."""
    return [
        NPCProfile(
            npc_id="captain",
            name="Captain Marcus",
            personality=PersonalityTraits(
                traits=["decisive", "authoritative"],
                big_five={},
            ),
            backstory="A seasoned expedition leader.",
            goals=["Ensure crew survival"],
            quirks=[],
            speech_patterns=SpeechPatterns(
                vocabulary=["crew", "safety"],
                tone="authoritative",
                formality="formal",
            ),
            voice_config=VoiceConfig(),
        ),
        NPCProfile(
            npc_id="doctor",
            name="Dr. Elena",
            personality=PersonalityTraits(
                traits=["compassionate", "analytical"],
                big_five={},
            ),
            backstory="A field medic with emergency experience.",
            goals=["Keep crew healthy"],
            quirks=[],
            speech_patterns=SpeechPatterns(
                vocabulary=["patient", "treatment"],
                tone="calm",
                formality="neutral",
            ),
            voice_config=VoiceConfig(),
        ),
        NPCProfile(
            npc_id="engineer",
            name="Engineer Alex",
            personality=PersonalityTraits(
                traits=["practical", "optimistic"],
                big_five={},
            ),
            backstory="A technical expert and problem solver.",
            goals=["Fix communication device"],
            quirks=[],
            speech_patterns=SpeechPatterns(
                vocabulary=["device", "repair"],
                tone="enthusiastic",
                formality="casual",
            ),
            voice_config=VoiceConfig(),
        ),
    ]


@pytest.fixture
def mock_npc_agents(sample_npc_profiles, mock_memory_system, mock_gemini_service):
    """Create mock NPC agents."""
    agents = {}
    for profile in sample_npc_profiles:
        agent = Mock(spec=NPCAgent)
        agent.initialize = Mock()
        agent.generate_response = Mock(return_value=f"Response from {profile.name}")
        agent.update_memory = Mock()
        agent.get_npc_id = Mock(return_value=profile.npc_id)
        agent.get_profile = Mock(return_value=profile)
        agents[profile.npc_id] = agent
    return agents


@pytest.fixture
def story_orchestrator(mock_npc_agents, mock_memory_system, mock_gemini_service):
    """Create a story orchestrator for testing."""
    return ConcreteStoryOrchestrator(
        npc_agents=mock_npc_agents,
        memory_system=mock_memory_system,
        gemini_service=mock_gemini_service,
        turn_strategy=TurnTakingStrategy.ROUND_ROBIN,
    )


@pytest.fixture
def story_config(sample_npc_profiles):
    """Create a story configuration for testing."""
    return StoryConfig(
        story_id="test_story",
        npc_profiles=sample_npc_profiles,
        initial_world_state={
            "day": 1,
            "weather": "snowy_and_cold",
        },
        story_settings={
            "scenario": "crashed_airship",
        },
    )


class TestStoryOrchestrator:
    """Tests for ConcreteStoryOrchestrator."""
    
    def test_start_story(self, story_orchestrator, story_config):
        """Test starting a new story."""
        world_state = story_orchestrator.start_story(story_config)
        
        assert world_state.story_id == story_config.story_id
        assert world_state.current_location == "bonfire_campsite"
        assert len(world_state.locations) >= 2  # Bonfire and crashed airship
        assert len(world_state.events) >= 1  # Initial crash event
        assert len(world_state.relationships) == len(story_config.npc_profiles)
    
    def test_get_state(self, story_orchestrator, story_config):
        """Test retrieving story state."""
        world_state = story_orchestrator.start_story(story_config)
        
        retrieved_state = story_orchestrator.get_state(story_config.story_id)
        assert retrieved_state is not None
        assert retrieved_state.story_id == story_config.story_id
    
    def test_get_state_nonexistent(self, story_orchestrator):
        """Test retrieving non-existent story state."""
        state = story_orchestrator.get_state("nonexistent_story")
        assert state is None
    
    def test_progress_story(self, story_orchestrator, story_config):
        """Test progressing the story."""
        world_state = story_orchestrator.start_story(story_config)
        
        initial_event_count = len(world_state.events)
        initial_timeline_count = len(world_state.timeline)
        
        # Progress story
        updated_state = story_orchestrator.progress_story(
            player_input=None,
            story_state=world_state,
        )
        
        # Should have more events (conversation turns)
        assert len(updated_state.events) > initial_event_count
        assert len(updated_state.timeline) > initial_timeline_count
    
    def test_create_expedition(self, story_orchestrator, story_config, mock_gemini_service):
        """Test creating and executing an expedition."""
        world_state = story_orchestrator.start_story(story_config)
        
        initial_event_count = len(world_state.events)
        
        # Mock Gemini response for expedition events
        mock_gemini_service.generate_content.return_value = """[
  {
    "event_type": "discovery",
    "description": "Found some metal scraps near the crash site.",
    "materials_found": {"metal_scraps": 3},
    "importance": 0.6
  }
]"""
        
        expedition = story_orchestrator.create_expedition(
            story_id=story_config.story_id,
            expedition_type=ExpeditionType.GATHER_MATERIALS,
            npc_ids=["engineer", "doctor"],
            goal="Gather materials for repairs",
        )
        
        assert expedition.expedition_id is not None
        assert expedition.expedition_type == ExpeditionType.GATHER_MATERIALS
        assert len(expedition.npc_ids) == 2
        assert expedition.completed_at is not None
        assert len(expedition.events) > 0
        
        # Check that world state was updated
        updated_state = story_orchestrator.get_state(story_config.story_id)
        assert len(updated_state.events) > initial_event_count
    
    def test_get_conversation_history(self, story_orchestrator, story_config):
        """Test getting conversation history."""
        world_state = story_orchestrator.start_story(story_config)
        
        # Progress story to generate conversation
        story_orchestrator.progress_story(
            player_input=None,
            story_state=world_state,
        )
        
        turns = story_orchestrator.get_conversation_history(story_config.story_id)
        assert len(turns) > 0
        assert all(turn.npc_id in ["captain", "doctor", "engineer"] for turn in turns)
    
    def test_get_expeditions(self, story_orchestrator, story_config, mock_gemini_service):
        """Test getting expeditions for a story."""
        world_state = story_orchestrator.start_story(story_config)
        
        # Mock Gemini response
        mock_gemini_service.generate_content.return_value = """[
  {
    "event_type": "success",
    "description": "Found useful materials.",
    "materials_found": {"wires": 2},
    "importance": 0.7
  }
]"""
        
        # Create expedition
        expedition = story_orchestrator.create_expedition(
            story_id=story_config.story_id,
            expedition_type=ExpeditionType.GATHER_MATERIALS,
            npc_ids=["engineer"],
            goal="Test expedition",
        )
        
        expeditions = story_orchestrator.get_expeditions(story_config.story_id)
        assert len(expeditions) == 1
        assert expeditions[0].expedition_id == expedition.expedition_id


class TestExpeditionSystem:
    """Tests for expedition system."""
    
    def test_expedition_creation(self):
        """Test creating an expedition."""
        expedition = Expedition(
            expedition_id="test_exp_1",
            expedition_type=ExpeditionType.GATHER_MATERIALS,
            npc_ids=["engineer"],
            goal="Gather materials",
        )
        
        assert expedition.expedition_id == "test_exp_1"
        assert expedition.expedition_type == ExpeditionType.GATHER_MATERIALS
        assert expedition.completed_at is None
        assert expedition.success is False
    
    def test_expedition_event(self):
        """Test creating an expedition event."""
        event = ExpeditionEvent(
            event_id="event_1",
            expedition_id="exp_1",
            event_type="discovery",
            description="Found materials",
            npc_id="engineer",
            materials_found={"metal_scraps": 3},
        )
        
        assert event.event_id == "event_1"
        assert event.is_shared is False
        assert event.materials_found == {"metal_scraps": 3}


class TestMultiPartyConversation:
    """Tests for multi-party conversation system."""
    
    def test_conversation_creation(self, mock_npc_agents, mock_gemini_service):
        """Test creating a multi-party conversation."""
        conversation = MultiPartyConversation(
            npc_agents=mock_npc_agents,
            turn_strategy=TurnTakingStrategy.ROUND_ROBIN,
            gemini_service=mock_gemini_service,
        )
        
        assert len(conversation.conversation_history) == 0
        assert len(conversation.turns) == 0
        assert conversation.current_turn_number == 0
    
    def test_add_turn(self, mock_npc_agents, mock_gemini_service):
        """Test adding a turn to conversation."""
        from src.models.conversation import ConversationContext
        
        conversation = MultiPartyConversation(
            npc_agents=mock_npc_agents,
            turn_strategy=TurnTakingStrategy.ROUND_ROBIN,
            gemini_service=mock_gemini_service,
        )
        
        context = ConversationContext(
            npc_id="captain",
            conversation_history=[],
            retrieved_memories=[],
            world_state={},
            player_input=None,
        )
        
        turn = conversation.add_turn(
            npc_id="captain",
            context=context,
            world_state={},
        )
        
        assert turn.npc_id == "captain"
        assert turn.turn_number == 1
        assert len(conversation.turns) == 1
        assert len(conversation.conversation_history) == 1
    
    def test_get_next_speaker_round_robin(self, mock_npc_agents, mock_gemini_service):
        """Test round-robin turn-taking."""
        conversation = MultiPartyConversation(
            npc_agents=mock_npc_agents,
            turn_strategy=TurnTakingStrategy.ROUND_ROBIN,
            gemini_service=mock_gemini_service,
        )
        
        available_npcs = ["captain", "doctor", "engineer"]
        
        # First speaker
        speaker1 = conversation.get_next_speaker(available_npcs, {})
        assert speaker1 in available_npcs
        
        # Add a turn
        from src.models.conversation import ConversationContext
        context = ConversationContext(
            npc_id=speaker1,
            conversation_history=[],
            retrieved_memories=[],
            world_state={},
        )
        conversation.add_turn(speaker1, context, {})
        
        # Next speaker should be different
        speaker2 = conversation.get_next_speaker(available_npcs, {})
        assert speaker2 != speaker1
        assert speaker2 in available_npcs

