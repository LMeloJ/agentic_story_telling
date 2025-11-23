"""
Dialog event data model for GUI integration.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class DialogEvent(BaseModel):
    """Dialog event for GUI display and TTS."""
    
    event_id: str = Field(..., description="Unique event identifier")
    npc_id: str = Field(..., description="NPC ID speaking")
    dialog_text: str = Field(..., description="Dialog text to display and speak")
    timestamp: datetime = Field(default_factory=datetime.now, description="Event timestamp")
    audio_file_path: Optional[str] = Field(default=None, description="Path to generated audio file")
    is_playing: bool = Field(default=False, description="Whether audio is currently playing")
    duration_seconds: Optional[float] = Field(default=None, description="Audio duration in seconds")

