"""
Utility functions for world state serialization.

Handles datetime serialization for JSON compatibility.
"""

from typing import Any, Dict
from datetime import datetime


def serialize_world_state(world_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively serialize datetime objects in world state to ISO format strings.
    
    Args:
        world_state: World state dictionary that may contain datetime objects
        
    Returns:
        World state dictionary with datetime objects serialized to strings
    """
    def _serialize(obj: Any) -> Any:
        """Recursively serialize datetime objects."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {key: _serialize(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [_serialize(item) for item in obj]
        elif isinstance(obj, tuple):
            return tuple(_serialize(item) for item in obj)
        else:
            return obj
    
    return _serialize(world_state)

