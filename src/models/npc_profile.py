"""
NPC Profile data model.
"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict


class PersonalityTraits(BaseModel):
    """Personality traits for an NPC."""
    
    traits: List[str] = Field(default_factory=list, description="List of personality trait keywords")
    big_five: Dict[str, float] = Field(
        default_factory=dict,
        description="Big Five personality scores (openness, conscientiousness, extraversion, agreeableness, neuroticism)"
    )


class SpeechPatterns(BaseModel):
    """Speech patterns and style for an NPC."""
    
    vocabulary: List[str] = Field(default_factory=list, description="Characteristic vocabulary words")
    tone: str = Field(default="neutral", description="Overall tone (enthusiastic, serious, casual, etc.)")
    formality: str = Field(default="neutral", description="Formality level (formal, casual, neutral)")


class VoiceConfig(BaseModel):
    """TTS voice configuration for an NPC."""
    
    voice_id: str = Field(default="default", description="Voice identifier (provider-specific)")
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Speech speed multiplier")
    pitch: float = Field(default=1.0, ge=0.5, le=2.0, description="Pitch multiplier")
    accent: str = Field(default="neutral", description="Accent or language variant")


class NPCProfile(BaseModel):
    """Complete NPC profile with personality, backstory, and configuration."""
    
    npc_id: str = Field(..., description="Unique identifier for the NPC")
    name: str = Field(..., description="Display name of the NPC")
    personality: PersonalityTraits = Field(..., description="Personality traits")
    backstory: str = Field(..., description="Character backstory and history")
    goals: List[str] = Field(default_factory=list, description="Current goals and motivations")
    quirks: List[str] = Field(default_factory=list, description="Character quirks and unique behaviors")
    speech_patterns: SpeechPatterns = Field(..., description="Speech patterns and style")
    voice_config: VoiceConfig = Field(..., description="TTS voice configuration")
    relationships: Dict[str, float] = Field(
        default_factory=dict,
        description="Relationships with other NPCs (NPC ID -> relationship score -1.0 to 1.0)"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "npc_id": "example_character_1",
                "name": "Example Character",
                "personality": {
                    "traits": ["curious", "friendly", "optimistic"],
                    "big_five": {
                        "openness": 0.8,
                        "conscientiousness": 0.6,
                        "extraversion": 0.7,
                        "agreeableness": 0.8,
                        "neuroticism": 0.3
                    }
                },
                "backstory": "A curious explorer who loves discovering new places and meeting new people.",
                "goals": ["Explore the world", "Help others"],
                "quirks": ["Always asks questions", "Enthusiastic about discoveries"],
                "speech_patterns": {
                    "vocabulary": ["wonderful", "amazing", "fascinating"],
                    "tone": "enthusiastic",
                    "formality": "casual"
                },
                "voice_config": {
                    "voice_id": "default",
                    "speed": 1.0,
                    "pitch": 1.0,
                    "accent": "neutral"
                },
                "relationships": {}
            }
        }
    )

