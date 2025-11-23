"""
Tests for data models (NPCProfile, Conversation, WorldState, Memory, DialogEvent).
"""

import pytest
from datetime import datetime
from typing import List

from src.models.npc_profile import NPCProfile, PersonalityTraits, SpeechPatterns, VoiceConfig
from src.models.conversation import Message, Conversation, ConversationContext
from src.models.world_state import WorldState, Location, Event, Relationship
from src.models.memory import MemoryChunk, MemoryMetadata
from src.models.dialog_event import DialogEvent


class TestNPCProfile:
    """Test NPCProfile model."""
    
    def test_create_npc_profile(self):
        """Test creating a valid NPC profile."""
        profile = NPCProfile(
            npc_id="test-npc-1",
            name="Test NPC",
            personality=PersonalityTraits(
                traits=["friendly", "curious"],
                big_five={"openness": 0.8, "conscientiousness": 0.7}
            ),
            backstory="A test character",
            goals=["Help the player"],
            speech_patterns=SpeechPatterns(),
            voice_config=VoiceConfig(),
        )
        
        assert profile.name == "Test NPC"
        assert profile.npc_id == "test-npc-1"
        assert len(profile.goals) == 1
    
    def test_npc_profile_validation(self):
        """Test NPC profile validation."""
        # Should raise error if required fields are missing
        with pytest.raises(Exception):
            NPCProfile()
    
    def test_personality_traits(self):
        """Test PersonalityTraits model."""
        traits = PersonalityTraits(
            traits=["curious", "friendly"],
            big_five={
                "openness": 0.8,
                "conscientiousness": 0.7,
                "extraversion": 0.6,
                "agreeableness": 0.9,
                "neuroticism": 0.3,
            }
        )
        
        assert traits.big_five["openness"] == 0.8
        assert traits.big_five["extraversion"] == 0.6
        assert "curious" in traits.traits
    
    def test_voice_config(self):
        """Test VoiceConfig model."""
        voice = VoiceConfig(
            voice_id="test-voice-1",
            speed=1.2,
            pitch=1.0,
            accent="american",
        )
        
        assert voice.voice_id == "test-voice-1"
        assert voice.speed == 1.2


class TestConversation:
    """Test Conversation models."""
    
    def test_create_message(self):
        """Test creating a message."""
        message = Message(
            role="user",
            content="Hello, NPC!",
            timestamp=datetime.now(),
        )
        
        assert message.role == "user"
        assert message.content == "Hello, NPC!"
        assert isinstance(message.timestamp, datetime)
    
    def test_create_conversation(self):
        """Test creating a conversation."""
        messages = [
            Message(role="user", content="Hello", timestamp=datetime.now()),
            Message(role="npc", content="Hi there!", timestamp=datetime.now()),
        ]
        
        conversation = Conversation(
            conversation_id="conv-1",
            npc_id="test-npc-1",
            messages=messages,
            context={"type": "test"},
        )
        
        assert conversation.npc_id == "test-npc-1"
        assert conversation.conversation_id == "conv-1"
        assert len(conversation.messages) == 2
    
    def test_conversation_context(self):
        """Test ConversationContext model."""
        context = ConversationContext(
            npc_id="test-npc-1",
            conversation_history=[],
            retrieved_memories=[],
            world_state={},
        )
        
        assert context.npc_id == "test-npc-1"
        assert isinstance(context.conversation_history, list)
        assert isinstance(context.retrieved_memories, list)


class TestWorldState:
    """Test WorldState models."""
    
    def test_create_location(self):
        """Test creating a location."""
        location = Location(
            location_id="loc-1",
            name="Test Location",
            description="A test location",
            properties={"type": "room"},
        )
        
        assert location.name == "Test Location"
        assert location.location_id == "loc-1"
        assert location.properties["type"] == "room"
    
    def test_create_event(self):
        """Test creating an event."""
        event = Event(
            event_id="event-1",
            event_type="conversation",
            description="A test event",
            timestamp=datetime.now(),
        )
        
        assert event.event_id == "event-1"
        assert event.event_type == "conversation"
    
    def test_create_relationship(self):
        """Test creating a relationship."""
        relationship = Relationship(
            npc_id_1="npc-1",
            npc_id_2="npc-2",
            relationship_score=0.8,
            relationship_type="friend",
        )
        
        assert relationship.npc_id_1 == "npc-1"
        assert relationship.relationship_score == 0.8
    
    def test_create_world_state(self):
        """Test creating a world state."""
        world_state = WorldState(
            story_id="story-1",
            locations={},
            events=[],
            relationships={},
        )
        
        assert world_state.story_id == "story-1"
        assert isinstance(world_state.locations, dict)
        assert isinstance(world_state.relationships, dict)


class TestMemory:
    """Test Memory models."""
    
    def test_create_memory_metadata(self):
        """Test creating memory metadata."""
        metadata = MemoryMetadata(
            npc_id="test-npc-1",
            conversation_id="conv-1",
            timestamp=datetime.now(),
            importance_score=0.8,
        )
        
        assert metadata.npc_id == "test-npc-1"
        assert metadata.importance_score == 0.8
    
    def test_create_memory_chunk(self):
        """Test creating a memory chunk."""
        chunk = MemoryChunk(
            chunk_id="chunk-1",
            content="Test memory content",
            embedding=[0.1, 0.2, 0.3],
            metadata=MemoryMetadata(
                npc_id="test-npc-1",
                conversation_id="conv-1",
                timestamp=datetime.now(),
                importance_score=0.8,
            ),
        )
        
        assert chunk.chunk_id == "chunk-1"
        assert len(chunk.embedding) == 3
        assert chunk.metadata.npc_id == "test-npc-1"


class TestDialogEvent:
    """Test DialogEvent model."""
    
    def test_create_dialog_event(self):
        """Test creating a dialog event."""
        event = DialogEvent(
            event_id="event-1",
            npc_id="test-npc-1",
            dialog_text="Hello, player!",
            timestamp=datetime.now(),
            audio_file_path="/path/to/audio.wav",
        )
        
        assert event.npc_id == "test-npc-1"
        assert event.event_id == "event-1"
        assert event.dialog_text == "Hello, player!"
        assert event.audio_file_path == "/path/to/audio.wav"

