"""
Script to create and run the crashed airship survival story scenario.

This script demonstrates Phase 4 story orchestration with:
- Multi-NPC conversations around a bonfire
- Expedition planning and execution
- Information sharing decisions
- World state management
"""

import json
import sys
from pathlib import Path
from typing import List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestration.story_config import StoryConfig
from src.orchestration.concrete_orchestrator import ConcreteStoryOrchestrator
from src.orchestration.expedition_system import ExpeditionType
from src.orchestration.multi_party_conversation import TurnTakingStrategy
from src.models.npc_profile import NPCProfile
from src.agents.langgraph_agent import LangGraphAgent
from src.memory.chromadb_memory_system import ChromaDBMemorySystem
from src.services.gemini_service import GeminiService
from src.services.logging_service import get_logger

logger = get_logger("crashed_airship_story")


def load_scenario_config(config_path: str) -> dict:
    """Load scenario configuration from JSON file."""
    with open(config_path, 'r') as f:
        return json.load(f)


def create_npc_profiles(config: dict) -> List[NPCProfile]:
    """Create NPCProfile objects from configuration."""
    profiles = []
    for profile_data in config["npc_profiles"]:
        profile = NPCProfile(**profile_data)
        profiles.append(profile)
    return profiles


def main():
    """Main function to run the crashed airship story."""
    logger.info("Starting crashed airship survival story scenario")
    
    # Load scenario configuration
    config_path = Path(__file__).parent.parent / "config" / "crashed_airship_scenario.json"
    if not config_path.exists():
        logger.error(f"Configuration file not found: {config_path}")
        return
    
    scenario_config = load_scenario_config(str(config_path))
    
    # Initialize services
    logger.info("Initializing services...")
    memory_system = ChromaDBMemorySystem()
    gemini_service = GeminiService()
    
    # Create NPC agents
    npc_agents = {}
    profiles = create_npc_profiles(scenario_config)
    
    for profile in profiles:
        agent = LangGraphAgent(
            memory_system=memory_system,
            gemini_service=gemini_service,
        )
        agent.initialize(profile.npc_id, profile)
        npc_agents[profile.npc_id] = agent
        logger.info(f"Initialized agent for {profile.name} ({profile.npc_id})")
    
    # Create story orchestrator
    orchestrator = ConcreteStoryOrchestrator(
        npc_agents=npc_agents,
        memory_system=memory_system,
        gemini_service=gemini_service,
        turn_strategy=TurnTakingStrategy.NATURAL,
    )
    
    # Create story configuration
    story_config = StoryConfig(
        story_id=scenario_config["story_id"],
        npc_profiles=profiles,
        initial_world_state=scenario_config["initial_world_state"],
        story_settings=scenario_config["story_settings"],
    )
    
    # Start story
    logger.info("Starting story...")
    world_state = orchestrator.start_story(story_config)
    logger.info(f"Story started. Current location: {world_state.current_location}")
    logger.info(f"Day: {world_state.story_progression.get('day', 1)}")
    
    # Simulate a conversation around the bonfire
    print("\n" + "="*80)
    print("CONVERSATION AROUND THE BONFIRE")
    print("="*80 + "\n")
    
    # Progress story (generate conversation)
    world_state = orchestrator.progress_story(
        player_input=None,
        story_state=world_state,
    )
    
    # Display conversation
    turns = orchestrator.get_conversation_history(story_config.story_id)
    for turn in turns:
        profile = next(p for p in profiles if p.npc_id == turn.npc_id)
        print(f"{profile.name}: {turn.message}\n")
    
    # Create an expedition
    print("\n" + "="*80)
    print("PLANNING AN EXPEDITION")
    print("="*80 + "\n")
    
    # Engineer suggests gathering materials
    expedition = orchestrator.create_expedition(
        story_id=story_config.story_id,
        expedition_type=ExpeditionType.GATHER_MATERIALS,
        npc_ids=["engineer", "doctor"],  # Captain can't go due to injury
        goal="Gather materials to fix the communication device",
    )
    
    print(f"Expedition completed: {expedition.expedition_id}")
    print(f"Success: {expedition.success}")
    print(f"Materials gathered: {expedition.materials_gathered}")
    print(f"\nEvents during expedition:")
    for event in expedition.events:
        print(f"  - {event.event_type}: {event.description}")
        if event.materials_found:
            print(f"    Materials found: {event.materials_found}")
    
    # Continue conversation after expedition
    print("\n" + "="*80)
    print("CONVERSATION AFTER EXPEDITION")
    print("="*80 + "\n")
    
    world_state = orchestrator.progress_story(
        player_input=None,
        story_state=world_state,
    )
    
    # Display new conversation turns
    all_turns = orchestrator.get_conversation_history(story_config.story_id)
    new_turns = all_turns[len(turns):]
    for turn in new_turns:
        profile = next(p for p in profiles if p.npc_id == turn.npc_id)
        print(f"{profile.name}: {turn.message}\n")
        if turn.shared_information:
            print(f"  [Shared information: {turn.shared_information.get('reasoning', 'N/A')}]")
    
    # Display final world state
    print("\n" + "="*80)
    print("FINAL WORLD STATE")
    print("="*80 + "\n")
    print(f"Day: {world_state.story_progression.get('day', 1)}")
    print(f"Materials collected: {world_state.story_progression.get('materials_collected', {})}")
    print(f"Total events: {len(world_state.events)}")
    print(f"Timeline: {len(world_state.timeline)} events")
    
    logger.info("Story scenario completed")


if __name__ == "__main__":
    main()

