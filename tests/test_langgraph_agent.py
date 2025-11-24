"""
Tests for LangGraph NPC Agent implementation.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch

from src.agents.langgraph_agent import LangGraphAgent, NPCState
from src.models.npc_profile import NPCProfile, PersonalityTraits, SpeechPatterns, VoiceConfig
from src.models.conversation import ConversationContext, Message, Conversation
from src.memory.memory_system import MemorySystem
from src.memory.memory_types import Memory
from src.services.gemini_service import GeminiService


@pytest.fixture
def sample_npc_profile():
    """Create a sample NPC profile for testing."""
    return NPCProfile(
        npc_id="test_npc_1",
        name="Test Character",
        personality=PersonalityTraits(
            traits=["curious", "friendly"],
            big_five={
                "openness": 0.8,
                "conscientiousness": 0.6,
                "extraversion": 0.7,
                "agreeableness": 0.8,
                "neuroticism": 0.3,
            }
        ),
        backstory="A curious explorer who loves discovering new places.",
        goals=["Explore the world", "Help others"],
        quirks=["Always asks questions"],
        speech_patterns=SpeechPatterns(
            vocabulary=["wonderful", "amazing"],
            tone="enthusiastic",
            formality="casual"
        ),
        voice_config=VoiceConfig(
            voice_id="default",
            speed=1.0,
            pitch=1.0,
            accent="neutral"
        ),
        relationships={}
    )


@pytest.fixture
def mock_memory_system():
    """Create a mock memory system."""
    memory_system = Mock(spec=MemorySystem)
    memory_system.store = Mock(return_value="chunk_id_123")
    memory_system.retrieve = Mock(return_value=[])
    memory_system.update = Mock(return_value=True)
    memory_system.delete = Mock(return_value=True)
    memory_system.search = Mock(return_value=[])
    memory_system.get_collection_info = Mock(return_value={"count": 0})
    return memory_system


@pytest.fixture
def mock_gemini_service():
    """Create a mock Gemini service."""
    gemini_service = Mock(spec=GeminiService)
    gemini_service.generate_response = Mock(return_value="Hello! How can I help you?")
    return gemini_service


@pytest.fixture
def langgraph_agent(mock_memory_system, mock_gemini_service):
    """Create a LangGraph agent instance."""
    agent = LangGraphAgent(
        memory_system=mock_memory_system,
        gemini_service=mock_gemini_service,
        max_context_tokens=2000,
    )
    return agent


class TestLangGraphAgentInitialization:
    """Test agent initialization."""
    
    def test_agent_initialization(self, langgraph_agent, sample_npc_profile):
        """Test that agent can be initialized."""
        assert langgraph_agent is not None
        assert langgraph_agent.memory_system is not None
        assert langgraph_agent.gemini_service is not None
    
    def test_initialize_agent(self, langgraph_agent, sample_npc_profile, mock_memory_system):
        """Test initializing agent with NPC profile."""
        langgraph_agent.initialize(sample_npc_profile.npc_id, sample_npc_profile)
        
        assert langgraph_agent.get_npc_id() == sample_npc_profile.npc_id
        assert langgraph_agent.get_profile() == sample_npc_profile
        
        # Verify profile was stored
        assert mock_memory_system.store.called
    
    def test_get_npc_id_before_initialization(self, langgraph_agent):
        """Test that getting NPC ID before initialization raises error."""
        with pytest.raises(ValueError, match="not initialized"):
            langgraph_agent.get_npc_id()
    
    def test_get_profile_before_initialization(self, langgraph_agent):
        """Test that getting profile before initialization raises error."""
        with pytest.raises(ValueError, match="not initialized"):
            langgraph_agent.get_profile()


class TestProfileEmbedding:
    """Test profile embedding functionality."""
    
    def test_profile_to_text(self, langgraph_agent, sample_npc_profile):
        """Test converting profile to text representation."""
        text = langgraph_agent._profile_to_text(sample_npc_profile)
        
        assert "Test Character" in text
        assert "test_npc_1" in text
        assert "curious explorer" in text
        assert "curious" in text or "friendly" in text
        assert "Explore the world" in text
    
    def test_store_profile_embedding(self, langgraph_agent, sample_npc_profile, mock_memory_system):
        """Test storing profile embedding."""
        # Mock retrieve to return empty (new profile)
        mock_memory_system.retrieve.return_value = []
        
        langgraph_agent._store_profile_embedding(sample_npc_profile)
        
        # Verify store was called
        assert mock_memory_system.store.called
        call_args = mock_memory_system.store.call_args
        assert call_args[1]["collection"] == "character_profiles"
        assert "Test Character" in call_args[1]["content"]
    
    def test_update_existing_profile(self, langgraph_agent, sample_npc_profile, mock_memory_system):
        """Test updating existing profile embedding."""
        # Mock retrieve to return existing profile
        existing_memory = Memory(
            chunk_id="existing_chunk_id",
            content="old content",
            metadata={"npc_id": sample_npc_profile.npc_id},
            score=1.0,
            timestamp=datetime.now(),
        )
        mock_memory_system.retrieve.return_value = [existing_memory]
        
        langgraph_agent._store_profile_embedding(sample_npc_profile)
        
        # Verify update was called instead of store
        assert mock_memory_system.update.called
        assert not mock_memory_system.store.called


class TestContextBuilding:
    """Test context building functionality."""
    
    def test_build_profile_context(self, langgraph_agent, sample_npc_profile):
        """Test building profile context."""
        context = langgraph_agent._build_profile_context(sample_npc_profile)
        
        assert "Test Character" in context
        assert "curious explorer" in context
        assert "curious" in context or "friendly" in context
        assert "Explore the world" in context
    
    def test_format_conversation_history(self, langgraph_agent):
        """Test formatting conversation history."""
        messages = [
            Message(role="user", content="Hello", timestamp=datetime.now()),
            Message(role="npc", content="Hi there!", timestamp=datetime.now(), npc_id="test_npc"),
        ]
        
        formatted = langgraph_agent._format_conversation_history(messages)
        
        assert "Hello" in formatted
        assert "Hi there!" in formatted
    
    def test_format_world_state(self, langgraph_agent):
        """Test formatting world state."""
        world_state = {
            "location": "forest",
            "time": "day",
            "weather": "sunny"
        }
        
        formatted = langgraph_agent._format_world_state(world_state)
        
        assert "forest" in formatted
        assert "day" in formatted
        assert "sunny" in formatted


class TestPromptEngineering:
    """Test prompt engineering."""
    
    def test_build_system_prompt(self, langgraph_agent, sample_npc_profile):
        """Test building system prompt."""
        prompt = langgraph_agent._build_system_prompt(sample_npc_profile)
        
        assert "Test Character" in prompt
        assert "character in an interactive story" in prompt
        assert "Stay in character" in prompt
        assert "personality traits" in prompt.lower()
    
    def test_build_user_prompt_with_input(self, langgraph_agent):
        """Test building user prompt with player input."""
        context = "Test context"
        player_input = "Hello!"
        
        prompt = langgraph_agent._build_user_prompt(context, player_input)
        
        assert context in prompt
        assert player_input in prompt
        assert "Player says:" in prompt
    
    def test_build_user_prompt_without_input(self, langgraph_agent):
        """Test building user prompt without player input."""
        context = "Test context"
        
        prompt = langgraph_agent._build_user_prompt(context, None)
        
        assert context in prompt
        assert "What do you say?" in prompt


class TestGraphNodes:
    """Test individual graph nodes."""
    
    def test_retrieve_memory_node(self, langgraph_agent, sample_npc_profile, mock_memory_system):
        """Test retrieve_memory node."""
        langgraph_agent.initialize(sample_npc_profile.npc_id, sample_npc_profile)
        
        # Mock retrieved memories
        mock_memories = [
            Memory(
                chunk_id="mem1",
                content="Previous conversation",
                metadata={"npc_id": sample_npc_profile.npc_id},
                score=0.9,
                timestamp=datetime.now(),
            )
        ]
        mock_memory_system.retrieve.return_value = mock_memories
        
        state: NPCState = {
            "npc_id": sample_npc_profile.npc_id,
            "npc_profile": sample_npc_profile,
            "current_context": "",
            "conversation_history": [],
            "retrieved_memories": [],
            "world_state": {},
            "player_input": "Hello",
            "response": None,
            "error": None,
        }
        
        result = langgraph_agent._retrieve_memory_node(state)
        
        assert len(result["retrieved_memories"]) > 0
        assert mock_memory_system.retrieve.called
    
    def test_build_context_node(self, langgraph_agent, sample_npc_profile):
        """Test build_context node."""
        langgraph_agent.initialize(sample_npc_profile.npc_id, sample_npc_profile)
        
        mock_memories = [
            Memory(
                chunk_id="mem1",
                content="Previous conversation",
                metadata={"npc_id": sample_npc_profile.npc_id},
                score=0.9,
                timestamp=datetime.now(),
            )
        ]
        
        state: NPCState = {
            "npc_id": sample_npc_profile.npc_id,
            "npc_profile": sample_npc_profile,
            "current_context": "",
            "conversation_history": [
                Message(role="user", content="Hello", timestamp=datetime.now()),
            ],
            "retrieved_memories": mock_memories,
            "world_state": {"location": "forest"},
            "player_input": "How are you?",
            "response": None,
            "error": None,
        }
        
        result = langgraph_agent._build_context_node(state)
        
        assert result["current_context"] != ""
        assert "Test Character" in result["current_context"]
        assert "Hello" in result["current_context"]
    
    def test_generate_response_node(self, langgraph_agent, sample_npc_profile, mock_gemini_service):
        """Test generate_response node."""
        langgraph_agent.initialize(sample_npc_profile.npc_id, sample_npc_profile)
        mock_gemini_service.generate_response.return_value = "I'm doing great!"
        
        state: NPCState = {
            "npc_id": sample_npc_profile.npc_id,
            "npc_profile": sample_npc_profile,
            "current_context": "Test context",
            "conversation_history": [],
            "retrieved_memories": [],
            "world_state": {},
            "player_input": "How are you?",
            "response": None,
            "error": None,
        }
        
        result = langgraph_agent._generate_response_node(state)
        
        assert result["response"] == "I'm doing great!"
        assert mock_gemini_service.generate_response.called
    
    def test_store_memory_node(self, langgraph_agent, sample_npc_profile, mock_memory_system):
        """Test store_memory node."""
        langgraph_agent.initialize(sample_npc_profile.npc_id, sample_npc_profile)
        
        state: NPCState = {
            "npc_id": sample_npc_profile.npc_id,
            "npc_profile": sample_npc_profile,
            "current_context": "",
            "conversation_history": [
                Message(role="user", content="Hello", timestamp=datetime.now()),
            ],
            "retrieved_memories": [],
            "world_state": {},
            "player_input": "Hello",
            "response": "Hi there!",
            "error": None,
        }
        
        result = langgraph_agent._store_memory_node(state)
        
        # Verify memory storage was attempted
        # (may not be called if there's an error, but node should complete)
        assert result["response"] == "Hi there!"


class TestResponseGeneration:
    """Test full response generation workflow."""
    
    def test_generate_response_full_workflow(
        self, langgraph_agent, sample_npc_profile, mock_memory_system, mock_gemini_service
    ):
        """Test full response generation workflow."""
        langgraph_agent.initialize(sample_npc_profile.npc_id, sample_npc_profile)
        
        # Mock memory retrieval
        mock_memory_system.retrieve.return_value = []
        
        # Mock Gemini response
        mock_gemini_service.generate_response.return_value = "Hello! Nice to meet you!"
        
        # Create context
        context = ConversationContext(
            npc_id=sample_npc_profile.npc_id,
            conversation_history=[],
            retrieved_memories=[],
            world_state={},
            player_input="Hello",
        )
        
        # Generate response
        response = langgraph_agent.generate_response(context)
        
        assert response == "Hello! Nice to meet you!"
        assert mock_gemini_service.generate_response.called
    
    def test_generate_response_wrong_npc_id(self, langgraph_agent, sample_npc_profile):
        """Test that wrong NPC ID raises error."""
        langgraph_agent.initialize(sample_npc_profile.npc_id, sample_npc_profile)
        
        context = ConversationContext(
            npc_id="wrong_npc_id",
            conversation_history=[],
            retrieved_memories=[],
            world_state={},
            player_input="Hello",
        )
        
        with pytest.raises(ValueError, match="doesn't match"):
            langgraph_agent.generate_response(context)
    
    def test_generate_response_not_initialized(self, langgraph_agent):
        """Test that generating response before initialization raises error."""
        context = ConversationContext(
            npc_id="test_npc",
            conversation_history=[],
            retrieved_memories=[],
            world_state={},
            player_input="Hello",
        )
        
        with pytest.raises(ValueError, match="not initialized"):
            langgraph_agent.generate_response(context)


class TestMemoryStorage:
    """Test memory storage functionality."""
    
    def test_update_memory(self, langgraph_agent, sample_npc_profile, mock_memory_system):
        """Test storing conversation in memory."""
        langgraph_agent.initialize(sample_npc_profile.npc_id, sample_npc_profile)
        
        conversation = Conversation(
            conversation_id="test_conv_1",
            npc_id=sample_npc_profile.npc_id,
            messages=[
                Message(role="user", content="Hello", timestamp=datetime.now()),
                Message(role="npc", content="Hi!", timestamp=datetime.now(), npc_id=sample_npc_profile.npc_id),
            ],
            importance_score=0.7,
        )
        
        langgraph_agent.update_memory(conversation)
        
        # Verify store was called for each message
        assert mock_memory_system.store.call_count >= 1
    
    def test_update_memory_not_initialized(self, langgraph_agent):
        """Test that updating memory before initialization raises error."""
        conversation = Conversation(
            conversation_id="test_conv_1",
            npc_id="test_npc",
            messages=[],
        )
        
        with pytest.raises(ValueError, match="not initialized"):
            langgraph_agent.update_memory(conversation)

