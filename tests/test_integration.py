"""
Integration tests for Phase 1 components working together.
"""

import pytest
from datetime import datetime
from pathlib import Path

from src.services.gemini_service import GeminiService
from src.services.tts_service import TTSService
from src.services.logging_service import get_logger
from src.models.npc_profile import NPCProfile, PersonalityTraits, VoiceConfig, SpeechPatterns
from src.models.conversation import Message, ConversationContext
from src.models.dialog_event import DialogEvent


class TestServiceIntegration:
    """Test services working together."""
    
    def test_gemini_and_tts_integration(self, test_config, temp_dir):
        """Test Gemini and TTS services working together."""
        gemini = GeminiService()
        tts = TTSService()
        logger = get_logger("integration_test")
        
        # Generate a response
        response = gemini.generate_response(
            prompt="Say hello",
            system_instruction="You are a friendly NPC",
        )
        
        assert response is not None
        logger.info(f"Generated response: {response}")
        
        # Convert to speech
        voice_config = VoiceConfig()
        audio_path = tts.generate_audio(response, voice_config)
        
        assert audio_path.exists()
        logger.info(f"Generated audio: {audio_path}")
    
    def test_npc_profile_to_dialog_flow(self, test_config, temp_dir):
        """Test flow from NPC profile to dialog event."""
        # Create NPC profile
        profile = NPCProfile(
            npc_id="test-npc-1",
            name="Test NPC",
            personality=PersonalityTraits(
                traits=["friendly", "helpful"],
                big_five={}
            ),
            backstory="A test character",
            goals=["Help players"],
            speech_patterns=SpeechPatterns(),
            voice_config=VoiceConfig(voice_id="test-voice", speed=1.0),
        )
        
        # Create conversation context
        context = ConversationContext(
            npc_id="test-npc-1",
            conversation_history=[
                Message(role="user", content="Hello", timestamp=datetime.now()),
            ],
            retrieved_memories=[],
            world_state={},
        )
        
        # Generate response (would use NPCAgent in real implementation)
        gemini = GeminiService()
        response = gemini.generate_response(
            prompt=context.conversation_history[-1].content,
            system_instruction=f"You are {profile.name}. {profile.personality}",
        )
        
        # Generate audio
        tts = TTSService()
        audio_path = tts.generate_audio(response, profile.voice_config)
        
        # Create dialog event
        dialog_event = DialogEvent(
            event_id="dialog-1",
            npc_id="test-npc-1",
            dialog_text=response,
            timestamp=datetime.now(),
            audio_file_path=str(audio_path),
        )
        
        assert dialog_event.npc_id == "test-npc-1"
        assert dialog_event.dialog_text == response
        assert Path(dialog_event.audio_file_path).exists()
    
    def test_error_handling_flow(self, test_config):
        """Test error handling across services."""
        logger = get_logger("error_test")
        
        # Test circuit breaker
        gemini = GeminiService()
        
        # In mock mode, should work fine
        try:
            response = gemini.generate_response("test")
            assert response is not None
            logger.info("Service handled request successfully")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            pytest.fail(f"Service should handle errors gracefully: {e}")

