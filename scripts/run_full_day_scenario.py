"""
Full day simulation of the crashed airship survival scenario.

This script simulates a complete day with:
- Morning planning conversation around the bonfire
- Expeditions to gather materials, food, water, and medicinal plants
- Evening debrief conversation where NPCs share their experiences
- World state updates throughout the day

Uses the actual Gemini API (not mocks).
"""

import json
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

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

logger = get_logger("full_day_scenario")


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


def print_section(title: str, width: int = 80):
    """Print a formatted section header."""
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width + "\n")


def print_conversation_turn(npc_name: str, message: str, shared_info: Dict[str, Any] = None):
    """Print a conversation turn in a formatted way."""
    print(f"💬 {npc_name}:")
    print(f"   {message}\n")
    if shared_info and shared_info.get("reasoning"):
        print(f"   [Sharing decision: {shared_info['reasoning']}]\n")


def print_expedition_results(expedition, npc_profiles: Dict[str, NPCProfile], world_state=None):
    """Print expedition results in a formatted way with quantitative details."""
    participants = ", ".join([
        npc_profiles[npc_id].name for npc_id in expedition.npc_ids
    ])
    print(f"📍 Expedition: {expedition.goal}")
    print(f"   Participants: {participants}")
    print(f"   Status: {'✅ Success' if expedition.success else '❌ Failed'}")
    
    # Show quantitative results
    if expedition.materials_gathered:
        print(f"\n   📦 Resources Gathered:")
        total_value = 0
        
        for material, quantity in expedition.materials_gathered.items():
            # Format based on material type
            if "water" in material.lower():
                print(f"      💧 Water: {quantity} liters")
                total_value += quantity * 2  # Water is very valuable
            elif "food" in material.lower():
                print(f"      🍖 Food: {quantity} units ({quantity} days for 1 person)")
                total_value += quantity * 3
            elif "medicine" in material.lower() or "dose" in material.lower():
                print(f"      💊 Medicine: {quantity} doses")
                total_value += quantity * 5  # Medicine is critical
            elif "metal" in material.lower() or "wire" in material.lower() or "component" in material.lower():
                print(f"      🔧 {material.replace('_', ' ').title()}: {quantity} units")
                total_value += quantity
            else:
                print(f"      📦 {material.replace('_', ' ').title()}: {quantity} units")
                total_value += quantity
        
        print(f"   Total Value: {total_value} points")
    
    # Show events with quantitative details
    if expedition.events:
        print(f"\n   📋 Events during expedition:")
        for event in expedition.events:
            print(f"      • {event.event_type.upper()}: {event.description}")
            if event.materials_found:
                found_items = []
                for mat, qty in event.materials_found.items():
                    if "water" in mat.lower():
                        found_items.append(f"{qty}L water")
                    elif "food" in mat.lower():
                        found_items.append(f"{qty} units food")
                    elif "medicine" in mat.lower() or "dose" in mat.lower():
                        found_items.append(f"{qty} doses medicine")
                    else:
                        found_items.append(f"{qty} {mat.replace('_', ' ')}")
                if found_items:
                    print(f"        💰 Found: {', '.join(found_items)}")
    
    # Show world state impact
    if world_state:
        print(f"\n   🌍 World State Impact:")
        progression = world_state.story_progression
        
        # Show resource levels
        if "water_liters" in progression:
            water = progression["water_liters"]
            level = progression.get("water_supplies", "low")
            print(f"      💧 Water: {water}L total ({level} supply)")
        
        if "food_units" in progression:
            food = progression["food_units"]
            level = progression.get("food_supplies", "low")
            print(f"      🍖 Food: {food} units total ({level} supply)")
        
        if "medicine_doses" in progression:
            medicine = progression["medicine_doses"]
            level = progression.get("medicine_supplies", "none")
            print(f"      💊 Medicine: {medicine} doses total ({level} supply)")
        
        # Show communication device progress
        materials = progression.get("materials_collected", {})
        comm_materials = {k: v for k, v in materials.items() if "metal" in k.lower() or "wire" in k.lower() or "component" in k.lower()}
        if comm_materials:
            total_comm = sum(comm_materials.values())
            print(f"      📡 Communication Device: {total_comm} repair materials collected")


def simulate_morning_planning(
    orchestrator: ConcreteStoryOrchestrator,
    story_id: str,
    world_state,
    npc_profiles: Dict[str, NPCProfile],
) -> Any:
    """Simulate morning planning conversation around the bonfire."""
    print_section("🌅 MORNING: Planning Around the Bonfire")
    
    print("The crew gathers around the bonfire to plan the day's activities...\n")
    time.sleep(1)
    
    # Generate morning conversation (5-6 turns)
    world_state = orchestrator.progress_story(
        player_input="Let's plan our day. What should we focus on?",
        story_state=world_state,
    )
    
    # Display conversation
    turns = orchestrator.get_conversation_history(story_id)
    morning_turns = turns[-5:] if len(turns) >= 5 else turns
    
    for turn in morning_turns:
        npc_name = npc_profiles[turn.npc_id].name
        print_conversation_turn(npc_name, turn.message, turn.shared_information)
        time.sleep(0.5)  # Small delay for readability
    
    return world_state


def simulate_expeditions(
    orchestrator: ConcreteStoryOrchestrator,
    story_id: str,
    world_state,
    npc_profiles: Dict[str, NPCProfile],
) -> List[Any]:
    """Simulate expeditions throughout the day."""
    print_section("🏃 EXPEDITIONS: Gathering Resources")
    
    expeditions = []
    
    # Expedition 1: Engineer and Doctor gather materials
    print("📡 Expedition 1: Gathering materials for communication device...")
    expedition1 = orchestrator.create_expedition(
        story_id=story_id,
        expedition_type=ExpeditionType.GATHER_MATERIALS,
        npc_ids=["engineer", "doctor"],  # Captain can't go due to injury
        goal="Gather metal scraps, wires, and electronic components to fix the communication device",
    )
    expeditions.append(expedition1)
    world_state = orchestrator.get_state(story_id)
    print_expedition_results(expedition1, npc_profiles, world_state)
    print()
    time.sleep(1)
    
    # Expedition 2: Doctor gathers medicinal plants
    print("🌿 Expedition 2: Searching for medicinal plants...")
    expedition2 = orchestrator.create_expedition(
        story_id=story_id,
        expedition_type=ExpeditionType.GATHER_MEDICINAL_PLANTS,
        npc_ids=["doctor"],
        goal="Find medicinal plants to treat the captain's injuries and prevent infection",
    )
    expeditions.append(expedition2)
    world_state = orchestrator.get_state(story_id)
    print_expedition_results(expedition2, npc_profiles, world_state)
    print()
    time.sleep(1)
    
    # Expedition 3: Engineer gathers food
    print("🍖 Expedition 3: Searching for food...")
    expedition3 = orchestrator.create_expedition(
        story_id=story_id,
        expedition_type=ExpeditionType.GATHER_FOOD,
        npc_ids=["engineer"],
        goal="Find food sources to sustain the crew",
    )
    expeditions.append(expedition3)
    world_state = orchestrator.get_state(story_id)
    print_expedition_results(expedition3, npc_profiles, world_state)
    print()
    time.sleep(1)
    
    # Expedition 4: Doctor gathers water
    print("💧 Expedition 4: Searching for clean water...")
    expedition4 = orchestrator.create_expedition(
        story_id=story_id,
        expedition_type=ExpeditionType.GATHER_WATER,
        npc_ids=["doctor"],
        goal="Find a source of clean, drinkable water",
    )
    expeditions.append(expedition4)
    world_state = orchestrator.get_state(story_id)
    print_expedition_results(expedition4, npc_profiles, world_state)
    print()
    
    return expeditions


def simulate_evening_debrief(
    orchestrator: ConcreteStoryOrchestrator,
    story_id: str,
    world_state,
    npc_profiles: Dict[str, NPCProfile],
    expeditions: List[Any],
) -> Any:
    """Simulate evening debrief conversation where NPCs share expedition experiences."""
    print_section("🌙 EVENING: Debrief Around the Bonfire")
    
    print("The crew returns to the bonfire to share their experiences and plan for tomorrow...\n")
    time.sleep(1)
    
    # Generate evening conversation (6-8 turns)
    # NPCs will share information about expeditions based on their decisions
    world_state = orchestrator.progress_story(
        player_input="Let's share what we found today and plan for tomorrow.",
        story_state=world_state,
    )
    
    # Display conversation
    all_turns = orchestrator.get_conversation_history(story_id)
    # Get turns from the last progress_story call
    previous_turn_count = len(all_turns) - 6  # Approximate previous count
    evening_turns = all_turns[previous_turn_count:] if previous_turn_count > 0 else all_turns[-6:]
    
    for turn in evening_turns:
        npc_name = npc_profiles[turn.npc_id].name
        print_conversation_turn(npc_name, turn.message, turn.shared_information)
        time.sleep(0.5)
    
    return world_state


def print_day_summary(world_state, expeditions: List[Any]):
    """Print a summary of the day's activities."""
    print_section("📊 DAY SUMMARY")
    
    progression = world_state.story_progression
    
    print(f"Day: {progression.get('day', 1)}")
    print(f"Weather: {progression.get('weather', 'Unknown')}")
    print(f"\nTotal Expeditions: {len(expeditions)}")
    print(f"Successful Expeditions: {sum(1 for exp in expeditions if exp.success)}")
    
    # Resource levels
    print(f"\n📦 RESOURCE LEVELS:")
    
    # Water
    water_liters = progression.get('water_liters', 0)
    water_level = progression.get('water_supplies', 'low')
    water_emoji = "💧" if water_level == "high" else "💧" if water_level == "medium" else "💧"
    print(f"   {water_emoji} Water: {water_liters}L ({water_level.upper()})")
    
    # Food
    food_units = progression.get('food_units', 0)
    food_level = progression.get('food_supplies', 'low')
    food_emoji = "🍖" if food_level == "high" else "🍖" if food_level == "medium" else "🍖"
    print(f"   {food_emoji} Food: {food_units} units ({food_level.upper()})")
    
    # Medicine
    medicine_doses = progression.get('medicine_doses', 0)
    medicine_level = progression.get('medicine_supplies', 'none')
    medicine_emoji = "💊" if medicine_level == "high" else "💊" if medicine_level == "medium" else "💊"
    print(f"   {medicine_emoji} Medicine: {medicine_doses} doses ({medicine_level.upper()})")
    
    # Communication device materials
    materials = progression.get('materials_collected', {})
    comm_materials = {k: v for k, v in materials.items() if "metal" in k.lower() or "wire" in k.lower() or "component" in k.lower()}
    if comm_materials:
        total_comm = sum(comm_materials.values())
        print(f"\n📡 COMMUNICATION DEVICE REPAIR:")
        print(f"   Materials collected: {total_comm} units")
        for mat, qty in comm_materials.items():
            print(f"      - {mat.replace('_', ' ').title()}: {qty}")
        comm_status = progression.get('communication_device_status', 'broken')
        print(f"   Status: {comm_status}")
    
    # Captain's condition
    print(f"\n👤 CREW STATUS:")
    captain_condition = progression.get('captain_condition', 'unknown')
    print(f"   Captain: {captain_condition}")
    
    print(f"\n📈 STATISTICS:")
    print(f"   Total Events: {len(world_state.events)}")
    print(f"   Timeline Events: {len(world_state.timeline)}")


def main():
    """Main function to run the full day scenario."""
    # Suppress verbose output
    import os
    import sys
    import warnings
    warnings.filterwarnings('ignore')
    
    # Disable progress bars from sentence-transformers and ChromaDB
    os.environ['TOKENIZERS_PARALLELISM'] = 'false'
    os.environ['TRANSFORMERS_VERBOSITY'] = 'error'
    
    # Suppress tqdm progress bars by redirecting stdout for tqdm
    class TqdmSuppress:
        def __init__(self, *args, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return True
        def update(self, *args):
            pass
        def close(self):
            pass
    
    # Set logging to WARNING level to reduce verbosity
    import logging
    logging.getLogger().setLevel(logging.WARNING)
    logging.getLogger("dynevi").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
    logging.getLogger("chromadb").setLevel(logging.ERROR)
    logging.getLogger("httpx").setLevel(logging.ERROR)
    logging.getLogger("httpcore").setLevel(logging.ERROR)
    
    # Try to suppress tqdm
    try:
        import tqdm
        # Monkey patch tqdm to suppress output
        original_tqdm = tqdm.tqdm
        def silent_tqdm(*args, **kwargs):
            kwargs['disable'] = True
            return original_tqdm(*args, **kwargs)
        tqdm.tqdm = silent_tqdm
    except ImportError:
        pass
    
    print_section("🚢 CRASHED AIRSHIP SURVIVAL SCENARIO - DAY 1", width=80)
    print("Simulating a full day of survival on a snowy island...")
    print("Using actual Gemini API for all interactions.\n")
    
    # Load scenario configuration
    config_path = Path(__file__).parent.parent / "config" / "crashed_airship_scenario.json"
    if not config_path.exists():
        logger.error(f"Configuration file not found: {config_path}")
        print(f"❌ Error: Configuration file not found at {config_path}")
        return
    
    try:
        scenario_config = load_scenario_config(str(config_path))
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        print(f"❌ Error loading configuration: {e}")
        return
    
    # Initialize services
    print("🔧 Initializing services...")
    try:
        memory_system = ChromaDBMemorySystem()
        gemini_service = GeminiService()
        print("✅ Services initialized")
        
        # Clear all previous memories before starting
        print("🧹 Clearing previous memories...")
        from src.memory.memory_utils import clear_all_memories
        clear_all_memories(memory_system)
        print("✅ Previous memories cleared\n")
    except Exception as e:
        logger.error(f"Error initializing services: {e}")
        print(f"❌ Error initializing services: {e}")
        print("Make sure you have GEMINI_API_KEY set in your environment.")
        return
    
    # Create NPC agents
    print("👥 Creating NPC agents...")
    npc_agents = {}
    profiles = create_npc_profiles(scenario_config)
    npc_profiles_dict = {profile.npc_id: profile for profile in profiles}
    
    for profile in profiles:
        try:
            agent = LangGraphAgent(
                memory_system=memory_system,
                gemini_service=gemini_service,
            )
            agent.initialize(profile.npc_id, profile)
            npc_agents[profile.npc_id] = agent
            print(f"  ✅ {profile.name} ({profile.npc_id})")
        except Exception as e:
            logger.error(f"Error initializing agent for {profile.npc_id}: {e}")
            print(f"  ❌ Error initializing {profile.name}: {e}")
            return
    
    print()
    
    # Create story orchestrator
    print("🎭 Creating story orchestrator...")
    try:
        orchestrator = ConcreteStoryOrchestrator(
            npc_agents=npc_agents,
            memory_system=memory_system,
            gemini_service=gemini_service,
            turn_strategy=TurnTakingStrategy.NATURAL,
        )
        print("✅ Story orchestrator created\n")
    except Exception as e:
        logger.error(f"Error creating orchestrator: {e}")
        print(f"❌ Error creating orchestrator: {e}")
        return
    
    # Create story configuration
    story_config = StoryConfig(
        story_id=scenario_config["story_id"],
        npc_profiles=profiles,
        initial_world_state=scenario_config["initial_world_state"],
        story_settings=scenario_config["story_settings"],
    )
    
    # Start story
    print("📖 Starting story...")
    try:
        world_state = orchestrator.start_story(story_config)
        print(f"✅ Story started: {world_state.story_id}")
        print(f"   Location: {world_state.current_location}")
        print(f"   Day: {world_state.story_progression.get('day', 1)}\n")
    except Exception as e:
        logger.error(f"Error starting story: {e}")
        print(f"❌ Error starting story: {e}")
        return
    
    # Simulate the day
    try:
        # Morning planning
        world_state = simulate_morning_planning(
            orchestrator, story_config.story_id, world_state, npc_profiles_dict
        )
        
        # Expeditions
        expeditions = simulate_expeditions(
            orchestrator, story_config.story_id, world_state, npc_profiles_dict
        )
        
        # Update world state after expeditions
        world_state = orchestrator.get_state(story_config.story_id)
        
        # Evening debrief
        world_state = simulate_evening_debrief(
            orchestrator, story_config.story_id, world_state, npc_profiles_dict, expeditions
        )
        
        # Final world state update
        world_state = orchestrator.get_state(story_config.story_id)
        
        # Day summary
        print_day_summary(world_state, expeditions)
        
        print_section("✅ DAY 1 SIMULATION COMPLETE", width=80)
        print("The crew has survived another day on the snowy island.")
        print("Their story continues...\n")
        
    except Exception as e:
        logger.error(f"Error during simulation: {e}")
        print(f"\n❌ Error during simulation: {e}")
        import traceback
        traceback.print_exc()
        return


if __name__ == "__main__":
    main()

